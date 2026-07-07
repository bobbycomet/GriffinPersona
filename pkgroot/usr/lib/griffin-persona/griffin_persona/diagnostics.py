"""
Griffin Persona — diagnostics engine.

Turns "install these 9 packages" into "click repair": each check below
returns one of OK / WARN / BAD plus, for anything not OK, a ready-made
request (apt packages or a user_action key) that the Repair button can
fire off without the person needing to know what's actually broken.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import detect


@dataclass
class CheckResult:
    id: str
    label: str
    status: str          # "ok" | "warn" | "bad"
    detail: str = ""
    fix_packages: list[str] | None = None
    fix_user_action: str | None = None


def _gpu_vendor() -> str:
    vendors = detect.primary_gpu_vendors()
    return vendors[0] if vendors else "unknown"


def run_all() -> list[CheckResult]:
    results: list[CheckResult] = []

    vk = detect.vulkan_status()
    results.append(CheckResult(
        "vulkan", "Vulkan available",
        "ok" if vk["vulkan"] else "bad",
        vk["detail"] or "vulkaninfo not found",
        fix_packages=["vulkan-tools", "libvulkan1"],
    ))
    results.append(CheckResult(
        "vulkan32", "Vulkan 32-bit",
        "ok" if vk["vulkan_i386"] else "warn",
        "" if vk["vulkan_i386"] else "libvulkan1:i386 missing — needed for most Wine/Proton titles",
        fix_packages=["libvulkan1:i386"],
    ))

    wine = detect.wine_status()
    results.append(CheckResult(
        "wine_installed", "Wine installed",
        "ok" if wine["installed"] else "bad",
        wine["version"],
        fix_packages=["wine"],
    ))

    prefix = detect.wine_prefix_health()
    results.append(CheckResult(
        "wine_prefix", "Wine prefix healthy",
        "ok" if prefix["healthy"] else ("warn" if not wine["installed"] else "bad"),
        prefix["path"],
        fix_user_action="repair:reset_prefix",
    ))

    results.append(CheckResult(
        "dxvk", "DXVK active",
        "ok" if detect.dxvk_active() else "warn",
        "Not detected in the default prefix",
        fix_user_action="install_dxvk",
    ))

    pw = detect.pipewire_status()
    results.append(CheckResult(
        "pipewire", "PipeWire detected",
        "ok" if pw["pipewire"] and pw["wireplumber"] else "bad",
        "wireplumber not running" if pw["pipewire"] and not pw["wireplumber"] else "",
        fix_packages=["pipewire", "pipewire-pulse", "wireplumber"],
    ))

    gm = detect.gamemode_status()
    results.append(CheckResult(
        "gamemode", "GameMode active",
        "ok" if gm["active"] else ("warn" if gm["installed"] else "bad"),
        "installed but not currently running a game" if gm["installed"] and not gm["active"] else "",
        fix_packages=["gamemode"],
    ))

    protons = detect.proton_installations()
    results.append(CheckResult(
        "proton", "Proton detected",
        "ok" if protons else "warn",
        ", ".join(protons) if protons else "No Steam compatibility tools found",
        fix_user_action="install_proton_ge",
    ))

    vcrun_ok = detect.vc_runtime_hint()
    results.append(CheckResult(
        "vcrun", "VC runtime present",
        "ok" if vcrun_ok else "warn",
        "" if vcrun_ok else "Missing VC runtime — many installers need this",
        fix_user_action="winetricks:vcrun2022",
    ))

    vendor = _gpu_vendor()
    drv = detect.gpu_driver_summary(vendor)
    results.append(CheckResult(
        "gpu_driver", "GPU driver present",
        "ok" if drv["driver_present"] else "bad",
        f"{vendor}: {drv['detail']}",
        fix_packages={"nvidia": ["nvidia-driver-550"], "amd": ["mesa-vulkan-drivers"],
                      "intel": ["mesa-vulkan-drivers"]}.get(vendor, []),
    ))

    vaapi = detect.vaapi_status(vendor)
    vaapi_fix_action = vaapi.get("fix_user_action")
    if vendor == "nvidia":
        status = "warn" if (not vaapi["available"] or vaapi_fix_action) else "ok"
        fix_packages = None
        fix_user_action = vaapi_fix_action or ("configure_nvidia_vaapi" if not vaapi["available"] else None)
    else:
        status = "ok" if vaapi["available"] else "warn"
        fix_packages = ["intel-media-va-driver-non-free", "vainfo"] if vendor == "intel" else ["mesa-va-drivers", "vainfo"]
        fix_user_action = None
    results.append(CheckResult(
        "hw_accel", "Hardware acceleration (VAAPI)",
        status,
        vaapi["detail"],
        fix_packages=fix_packages,
        fix_user_action=fix_user_action,
    ))

    return results


def repairable(results: list[CheckResult]) -> list[CheckResult]:
    return [r for r in results if r.status != "ok" and (r.fix_packages or r.fix_user_action)]
