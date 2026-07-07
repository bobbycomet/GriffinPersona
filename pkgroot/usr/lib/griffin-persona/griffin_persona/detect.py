"""
Griffin Persona — detection layer.

Everything here is read-only and runs unprivileged in the GUI process:
lspci parsing, `command -v` checks, dpkg queries, and small probe binaries
like vulkaninfo. Nothing in this module changes the system. This is the
"detect" half of the "detect -> select profile -> preview -> apply" flow
the rest of the app is built around.
"""

from __future__ import annotations

import functools
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

PCI_VENDOR_NVIDIA = "10de"
PCI_VENDOR_AMD = "1002"
PCI_VENDOR_INTEL = "8086"


def _run(cmd: list[str], timeout: int = 5, extra_env: dict | None = None) -> tuple[int, str]:
    env = {**os.environ, **extra_env} if extra_env else None
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL, env=env,
        )
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 1, ""


def which(binary: str) -> bool:
    return shutil.which(binary) is not None


@dataclass
class GpuDevice:
    vendor: str       # "nvidia" | "amd" | "intel" | "unknown"
    name: str
    pci_slot: str = ""


@functools.lru_cache(maxsize=1)
def detect_gpus() -> list[GpuDevice]:
    """Parse `lspci -nnk` for display controllers. Cached for process lifetime."""
    rc, out = _run(["lspci", "-nnk"])
    gpus: list[GpuDevice] = []
    if rc != 0 or not out:
        return gpus
    for line in out.splitlines():
        if "VGA compatible controller" not in line and "3D controller" not in line:
            continue
        slot = line.split()[0]
        vendor = "unknown"
        if f"[{PCI_VENDOR_NVIDIA}:" in line:
            vendor = "nvidia"
        elif f"[{PCI_VENDOR_AMD}:" in line:
            vendor = "amd"
        elif f"[{PCI_VENDOR_INTEL}:" in line:
            vendor = "intel"
        name = line.split(": ", 1)[-1]
        gpus.append(GpuDevice(vendor=vendor, name=name, pci_slot=slot))
    return gpus


def primary_gpu_vendors() -> list[str]:
    seen = []
    for gpu in detect_gpus():
        if gpu.vendor != "unknown" and gpu.vendor not in seen:
            seen.append(gpu.vendor)
    return seen or ["unknown"]


def is_hybrid_graphics() -> bool:
    """True when more than one GPU vendor is present, e.g. Intel iGPU + NVIDIA dGPU."""
    return len(set(primary_gpu_vendors()) - {"unknown"}) > 1


KERNEL_AUTOTUNE_STATE_PATH = Path("/etc/kernel-autotune/state.json")

# DMI chassis types that mean "this is portable" (SMBIOS spec). 8=Portable,
# 9=Laptop, 10=Notebook, 11=Hand Held, 14=Sub Notebook, 31=Convertible,
# 32=Detachable. Everything else (3=Desktop, 4=Low Profile Desktop,
# 6/7=Mini/Mid Tower, 13=All in One, 23=Rack Mount, 24=Sealed-case PC, etc)
# is treated as not-a-laptop.
_LAPTOP_CHASSIS_TYPES = {8, 9, 10, 11, 14, 31, 32}


def read_kernel_autotune_state() -> dict | None:
    """
    Reads /etc/kernel-autotune/state.json if present. This file is written
    and owned by Kernel Auto-tune, not by Griffin Persona -- read-only here.
    Used purely to (a) trust an already-known device_type rather than
    re-detecting it, and (b) show the person that the system already knows
    their machine (hostname, kernel, CPU, GPU, driver) on the GPU & Drivers
    page, which is a trust-building display, not something this app acts on.
    """
    if not KERNEL_AUTOTUNE_STATE_PATH.exists():
        return None
    try:
        return json.loads(KERNEL_AUTOTUNE_STATE_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _detect_laptop_fallback() -> bool:
    """
    Used only when Kernel Auto-tune's state.json isn't present or doesn't
    have a usable device_type. DMI chassis type is checked first since it's
    purpose-built for exactly this (every laptop BIOS reports one of the
    portable chassis codes); battery presence is the fallback for the rare
    case chassis type is missing/unreliable. Neither is perfect (a desktop
    with a UPS battery reported oddly, a chassis type a vendor got wrong),
    but combined they're right for the overwhelming majority of machines.
    """
    chassis_path = Path("/sys/class/dmi/id/chassis_type")
    if chassis_path.exists():
        try:
            chassis = int(chassis_path.read_text().strip())
            if chassis in _LAPTOP_CHASSIS_TYPES:
                return True
        except (ValueError, OSError):
            pass

    power_supply_dir = Path("/sys/class/power_supply")
    if power_supply_dir.exists():
        try:
            return any(entry.name.startswith("BAT") for entry in power_supply_dir.iterdir())
        except OSError:
            pass
    return False


def device_type() -> dict:
    """
    Returns {"type": "laptop"|"desktop", "source": "kernel-autotune"|"detected"}.

    Prefers Kernel Auto-tune's own state.json when it has a usable
    device_type, since that tool already did this work; falls back to
    independent detection (DMI chassis type, then battery presence) when
    the file is missing or doesn't say.
    """
    state = read_kernel_autotune_state()
    if state and state.get("device_type") in ("laptop", "desktop"):
        return {"type": state["device_type"], "source": "kernel-autotune"}
    return {"type": "laptop" if _detect_laptop_fallback() else "desktop", "source": "detected"}


@functools.lru_cache(maxsize=1)
def dpkg_installed_packages() -> set[str]:
    rc, out = _run(["dpkg-query", "-f", "${binary:Package}\n", "-W"], timeout=15)
    if rc != 0:
        return set()
    return set(out.splitlines())


def is_package_installed(name: str) -> bool:
    return name in dpkg_installed_packages()


def i386_arch_enabled() -> bool:
    rc, out = _run(["dpkg", "--print-foreign-architectures"])
    return "i386" in out.split()


def vulkan_status() -> dict:
    status = {"vulkan": False, "vulkan_i386": False, "detail": ""}
    if which("vulkaninfo"):
        rc, out = _run(["vulkaninfo", "--summary"], timeout=10)
        status["vulkan"] = rc == 0 and "deviceName" in out
        status["detail"] = out.strip().splitlines()[-1] if out.strip() else ""
    status["vulkan_i386"] = is_package_installed("libvulkan1:i386")
    return status


def wine_status() -> dict:
    info = {"installed": which("wine"), "version": ""}
    if info["installed"]:
        rc, out = _run(["wine", "--version"])
        info["version"] = out.strip()
    return info


def wine_prefix_health(prefix: str | None = None) -> dict:
    prefix_path = Path(prefix or os.environ.get("WINEPREFIX", str(Path.home() / ".wine")))
    exists = prefix_path.exists()
    healthy = exists and (prefix_path / "system.reg").exists() and (prefix_path / "drive_c").is_dir()
    return {"path": str(prefix_path), "exists": exists, "healthy": healthy}


def dxvk_active(prefix: str | None = None) -> bool:
    prefix_path = Path(prefix or os.environ.get("WINEPREFIX", str(Path.home() / ".wine")))
    dll = prefix_path / "drive_c" / "windows" / "system32" / "d3d11.dll"
    if not dll.exists():
        return False
    rc, out = _run(["file", str(dll)])
    return "PE32" in out  # DXVK ships a real PE dll; absence of one usually means unset


def pipewire_status() -> dict:
    rc1, _ = _run(["pgrep", "-x", "pipewire"])
    rc2, _ = _run(["pgrep", "-x", "wireplumber"])
    return {"pipewire": rc1 == 0, "wireplumber": rc2 == 0}


def gamemode_status() -> dict:
    installed = which("gamemoded") or is_package_installed("gamemode")
    rc, _ = _run(["pgrep", "-x", "gamemoded"])
    return {"installed": installed, "active": rc == 0}


def proton_installations() -> list[str]:
    found = []
    candidates = [
        Path.home() / ".steam" / "root" / "compatibilitytools.d",
        Path.home() / ".local" / "share" / "Steam" / "compatibilitytools.d",
        Path.home() / ".steam" / "steam" / "steamapps" / "common",
    ]
    for c in candidates:
        if c.exists():
            for child in c.iterdir():
                if "proton" in child.name.lower():
                    found.append(child.name)
    return sorted(set(found))


def lutris_wine_ge_installed() -> list[str]:
    base = Path.home() / ".local" / "share" / "lutris" / "runners" / "wine"
    if not base.exists():
        return []
    return sorted(p.name for p in base.iterdir() if "ge" in p.name.lower())


def vc_runtime_hint(prefix: str | None = None) -> bool:
    """Best-effort: is a vcrun-style mfc/msvcp dll present in the prefix."""
    prefix_path = Path(prefix or os.environ.get("WINEPREFIX", str(Path.home() / ".wine")))
    sysdir = prefix_path / "drive_c" / "windows" / "system32"
    if not sysdir.exists():
        return False
    return any((sysdir / n).exists() for n in ("msvcp140.dll", "vcruntime140.dll"))


def gpu_driver_summary(vendor: str) -> dict:
    """Quick read of what's currently on disk for a given vendor, for the diagnostics page."""
    if vendor == "nvidia":
        rc, out = _run(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"])
        return {"driver_present": rc == 0, "detail": out.strip()}
    if vendor == "amd":
        return {"driver_present": is_package_installed("mesa-vulkan-drivers"), "detail": "Mesa RADV"}
    if vendor == "intel":
        return {"driver_present": is_package_installed("mesa-vulkan-drivers"), "detail": "Mesa ANV"}
    return {"driver_present": False, "detail": ""}


def nvidia_recommended_driver() -> str | None:
    """
    Read-only preview helper: asks `ubuntu-drivers devices` (unprivileged)
    which package it would pick, WITHOUT installing anything. The actual
    install (op_install_nvidia_driver_auto in the helper) re-derives this
    itself as root rather than trusting this string — this function exists
    purely so the preview dialog can tell the person what's about to
    happen, instead of hardcoding a driver version that goes stale.
    """
    rc, out = _run(["ubuntu-drivers", "devices"], timeout=15)
    if rc != 0:
        return None
    for line in out.splitlines():
        if "recommended" in line and "nvidia-driver-" in line:
            for token in line.split():
                if token.startswith("nvidia-driver-"):
                    return token
    return None


def find_nvidia_render_node(base: str | Path = "/sys/class/drm") -> str | None:
    """
    Walks /sys/class/drm/renderD*/device/vendor to find the render node
    backed by an NVIDIA GPU (PCI vendor 0x10de). Only meaningful when more
    than one GPU is present — on a single-NVIDIA-GPU system there's
    nothing to disambiguate, vaapi_status() never even calls this there.
    """
    drm_dir = Path(base)
    if not drm_dir.exists():
        return None
    try:
        entries = sorted(drm_dir.iterdir())
    except OSError:
        return None
    for entry in entries:
        if not entry.name.startswith("renderD"):
            continue
        try:
            vendor = (entry / "device" / "vendor").read_text().strip().lower()
        except OSError:
            continue
        if vendor == "0x10de":
            return f"/dev/dri/{entry.name}"
    return None


def vaapi_status(vendor: str | None = None) -> dict:
    """
    Actually runs vainfo rather than guessing from a package name — the
    package that provides a working VA-API driver varies by vendor and by
    distro (mesa-va-drivers, intel-media-va-driver-non-free, i965-va-driver,
    nvidia-vaapi-driver, ...), so checking for one specific name is wrong
    for everyone else. vainfo's own success/failure is the only thing
    that's actually true across all of them.

    NVIDIA is a special case: its proprietary driver has no native VA-API
    support at all. The only way to get VA-API on NVIDIA is the community
    nvidia-vaapi-driver bridge (NVDEC underneath), and libva will not find
    it through auto-detection — it needs LIBVA_DRIVER_NAME=nvidia and (on
    driver 525+) NVD_BACKEND=direct set when the probe runs. Setting these
    here, rather than relying on the parent process's environment, also
    means this check works immediately after applying the fix instead of
    needing a logout/login first — even though /etc/environment itself
    (which is what real apps like Firefox or mpv pick up) does need that
    relogin to take effect for them.

    Also sets NVD_LOG=1 for NVIDIA: a bare vainfo failure ("init failed")
    is the same generic message for at least two unrelated root causes —
    a hybrid-graphics setup probing the wrong DRM render node, vs. an
    actual CUDA initialization failure — and only the verbose log tells
    them apart.

    On systems with more than one GPU, the DEFAULT probe goes through
    whatever render node the display stack picked, which is frequently
    the integrated GPU rather than NVIDIA — that's exactly the "Invalid
    driver for DRM device" failure. If that happens AND more than one GPU
    is present, this retries once with --display drm --device pointed
    explicitly at the render node that sysfs reports as NVIDIA, so a
    hybrid system that's actually fine doesn't get reported as broken
    just because the default device guess was wrong. The result says so
    explicitly, because pointing our own probe at the right device doesn't
    mean every app will — there's no single env var that reliably does
    that for arbitrary applications, so the result is honest about the
    distinction rather than claiming a universal fix that doesn't exist.

    On a single-GPU NVIDIA system none of this multi-GPU branch ever runs
    at all — it's a complete no-op there.

    Deliberately does NOT key off the words "error"/"failed" anywhere in
    the output: libva prints benign warnings containing those words (e.g.
    "error: XDG_RUNTIME_DIR not set") even on a perfectly working driver.
    A successful vaInitialize always prints a "Driver version:" line
    followed by a list of supported VAProfiles — that combination is the
    only thing treated as a positive result; everything else is "not
    available", with whatever specific reason could be extracted from the
    log as the detail.
    """
    if not which("vainfo"):
        return {"available": False, "detail": "vainfo not installed"}
    extra_env = {"LIBVA_DRIVER_NAME": "nvidia", "NVD_BACKEND": "direct", "NVD_LOG": "1"} \
        if vendor == "nvidia" else None
    _, out = _run(["vainfo"], timeout=8, extra_env=extra_env)
    lines = out.splitlines()
    driver_line = next((l for l in lines if "Driver version" in l), None)
    if driver_line and "VAProfile" in out:
        return {"available": True, "detail": driver_line.strip()}

    if vendor == "nvidia":
        if len(detect_gpus()) > 1:
            node = find_nvidia_render_node()
            if node:
                _, out2 = _run(["vainfo", "--display", "drm", "--device", node],
                                timeout=8, extra_env=extra_env)
                driver_line2 = next((l for l in out2.splitlines() if "Driver version" in l), None)
                if driver_line2 and "VAProfile" in out2:
                    return {
                        "available": True,
                        "detail": f"{driver_line2.strip()} — works on the NVIDIA GPU directly "
                                  f"({node}). This is a hybrid system, so individual apps may "
                                  f"still default to your integrated GPU unless configured to "
                                  f"prefer the NVIDIA one; there's no single setting here that "
                                  f"guarantees every app picks it.",
                    }

        # The Direct backend talks to the NVIDIA kernel module through its own
        # low-level resource-manager ioctls, separately from CUDA or DRM
        # device selection. On some driver/GPU combinations that fails right
        # at the first allocation (NV01_ROOT_CLIENT) — a currently open,
        # unresolved upstream bug (elFarto/nvidia-vaapi-driver#392), not
        # something fixable from here. EGL is the original backend and uses
        # a different code path entirely, so it's worth an actual retry
        # rather than just reporting the Direct-backend failure as final.
        if "NV01_ROOT_CLIENT failed" in out or "nv_alloc_object failed" in out:
            egl_env = {**extra_env, "NVD_BACKEND": "egl"}
            _, out_egl = _run(["vainfo"], timeout=8, extra_env=egl_env)
            driver_line_egl = next((l for l in out_egl.splitlines() if "Driver version" in l), None)
            if driver_line_egl and "VAProfile" in out_egl:
                result = {
                    "available": True,
                    "detail": f"{driver_line_egl.strip()} — the Direct backend fails on this "
                              f"driver/GPU combination with a low-level error that's an open, "
                              f"unresolved upstream issue (nvidia-vaapi-driver#392); the older "
                              f"EGL backend works fine instead.",
                }
                if _read_etc_environment_value("NVD_BACKEND") != "egl":
                    result["fix_user_action"] = "set_nvidia_vaapi_backend:egl"
                    result["detail"] += (" Your saved configuration still says 'direct' — "
                                          "click Repair to switch it to 'egl' so real apps "
                                          "get a working backend too.")
                return result

        detail = _diagnose_nvidia_vaapi_failure(out)
        if detail:
            return {"available": False, "detail": detail}
    detail = next((l.strip() for l in lines if l.strip().lower().startswith("vainfo:")), "")
    if vendor == "nvidia" and not detail:
        detail = "NVIDIA's proprietary driver has no native VA-API support without nvidia-vaapi-driver installed"
    return {"available": False, "detail": detail or "vainfo did not report a working driver"}


def _read_etc_environment_value(key: str, path: str | Path = "/etc/environment") -> str | None:
    p = Path(path)
    if not p.exists():
        return None
    try:
        for line in p.read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return None


def _diagnose_nvidia_vaapi_failure(nvd_log_output: str) -> str | None:
    """
    Translates the most common nvidia-vaapi-driver NVD_LOG=1 failure
    signatures into a specific, actionable message. Returns None if the
    output doesn't match a known pattern, so the caller can fall back to
    a generic message rather than print something potentially wrong.
    """
    m = re.search(r"Invalid driver for DRM device:\s*(\S+)", nvd_log_output)
    if m:
        return (f"VA-API tried to use your {m.group(1)} GPU instead of the NVIDIA one — "
                f"this happens on hybrid-graphics systems (laptop with both an integrated "
                f"and a discrete GPU). The render node it picked by default isn't the "
                f"NVIDIA card.")
    if "NV01_ROOT_CLIENT failed" in nvd_log_output or "nv_alloc_object failed" in nvd_log_output:
        return ("The Direct backend failed at a low level (NV01_ROOT_CLIENT) talking to the "
                "NVIDIA kernel driver, and the EGL backend was tried as a fallback but also "
                "failed. This matches an open, unresolved upstream bug "
                "(elFarto/nvidia-vaapi-driver issue #392) on some driver/GPU combinations, "
                "not something this app can patch from here.")
    m = re.search(r"CUDA ERROR '([^']*)'\s*\((\d+)\)", nvd_log_output)
    if m:
        return (f"CUDA failed to initialize ({m.group(1)}, code {m.group(2)}) — "
                f"often means nvidia-persistenced isn't running or the nvidia-uvm "
                f"kernel module isn't loaded.")
    if "Exporter failed" in nvd_log_output:
        return "The driver loaded but failed during initialization (Exporter failed) — see full log for details."
    return None


def flatpak_available() -> bool:
    return which("flatpak")


def timeshift_available() -> bool:
    return which("timeshift")


def is_btrfs_root() -> bool:
    rc, out = _run(["findmnt", "-no", "FSTYPE", "/"])
    return out.strip() == "btrfs"
