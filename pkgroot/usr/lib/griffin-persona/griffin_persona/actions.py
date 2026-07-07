"""
Griffin Persona — action orchestration.

Pages hand this module a list of selected ``Component`` objects. It figures
out, per component, whether the change needs root (and if so builds the
exact request the privileged helper expects) or can run unprivileged in the
GUI process (downloading Wine-GE/Proton-GE into the user's own home
directory, running winetricks against a user prefix, a `flatpak --user`
install, etc).

This is also where the "preview before apply" promise gets kept: callers
should render `describe_plan()` to the person before ever calling
`apply_plan()`.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from . import detect, state
from .packages import Component
from .privileged import run_privileged_streaming

# user_action keys that require root, mapped to the exact helper request
# (without "label", which callers fill in per-component).
PRIVILEGED_USER_ACTIONS: dict[str, dict] = {
    "enable_i386": {"action": "enable_i386"},
    "install_nvidia_driver_auto": {"action": "install_nvidia_driver_auto"},
    "configure_nvidia_vaapi": {"action": "configure_nvidia_vaapi"},
    "install_winehq_stable": {"action": "add_repo_and_install", "repo_id": "winehq-stable"},
    "install_winehq_staging": {"action": "add_repo_and_install", "repo_id": "winehq-staging"},
    "install_lact": {"action": "install_release_app", "app_id": "lact"},
    "install_sunshine": {"action": "install_release_app", "app_id": "sunshine"},
    "install_vscode_repo": {"action": "add_repo_and_install", "repo_id": "vscode"},
    "install_docker_repo": {"action": "add_repo_and_install", "repo_id": "docker"},
    "install_firefox_repo": {"action": "add_repo_and_install", "repo_id": "firefox-mozilla"},
    "install_brave_repo": {"action": "add_repo_and_install", "repo_id": "brave-browser"},
    "install_vivaldi_repo": {"action": "add_repo_and_install", "repo_id": "vivaldi"},
    "install_opentabletdriver": {"action": "install_release_app", "app_id": "opentabletdriver"},
}

GITHUB_API = "https://api.github.com/repos/{repo}/releases/latest"


@dataclass
class Plan:
    packages: list[str] = field(default_factory=list)
    privileged_actions: list[dict] = field(default_factory=list)
    unprivileged: list[Component] = field(default_factory=list)
    needs_i386: bool = False


def build_plan(components: list[Component]) -> Plan:
    plan = Plan()
    for c in components:
        if c.packages:
            plan.packages.extend(c.packages)
            if c.requires_i386:
                plan.needs_i386 = True
        elif c.user_action and c.user_action.startswith("set_nvidia_vaapi_backend:"):
            backend = c.user_action.split(":", 1)[1]
            plan.privileged_actions.append(
                {"action": "set_nvidia_vaapi_backend", "backend": backend, "label": c.name}
            )
        elif c.user_action and c.user_action.startswith("toggle_snap:"):
            enable = c.user_action.split(":", 1)[1] == "on"
            plan.privileged_actions.append(
                {"action": "toggle_snap", "enable": enable, "label": c.name}
            )
        elif c.user_action in PRIVILEGED_USER_ACTIONS:
            req = dict(PRIVILEGED_USER_ACTIONS[c.user_action])
            req["label"] = c.name
            plan.privileged_actions.append(req)
        elif c.user_action:
            plan.unprivileged.append(c)
    plan.packages = sorted(set(plan.packages))
    return plan


def describe_plan(plan: Plan) -> str:
    """Human-readable preview shown before Apply — 'here's exactly what changes'."""
    lines = []
    if plan.needs_i386:
        lines.append("• Enable 32-bit (i386) package architecture")
    if plan.packages:
        lines.append("• Install via apt: " + ", ".join(plan.packages))
    action_hint = {
        "enable_i386": "requires admin",
        "add_repo_and_install": "adds a software source, requires admin",
        "install_release_app": "downloads and installs a .deb, requires admin",
        "toggle_snap": "requires admin",
        "install_nvidia_driver_auto": "requires admin",
        "configure_nvidia_vaapi": "installs nvidia-vaapi-driver and edits /etc/environment, requires admin",
        "set_nvidia_vaapi_backend": "edits /etc/environment, requires admin",
    }
    for action in plan.privileged_actions:
        if action["action"] == "install_nvidia_driver_auto":
            detected = detect.nvidia_recommended_driver()
            suffix = f" (auto-detected: {detected})" if detected else " (auto-detected at apply time)"
            lines.append(f"• {action.get('label', 'NVIDIA proprietary driver')}{suffix} — requires admin")
            continue
        hint = action_hint.get(action["action"], "requires admin")
        lines.append(f"• {action.get('label', action['action'])} ({hint})")
    for c in plan.unprivileged:
        lines.append(f"• {c.name} — {c.description}")
    if not lines:
        return "Nothing selected."
    return "\n".join(lines)


def apply_plan(plan: Plan, on_line=None, wine_prefix: str | None = None) -> tuple[bool, list[str]]:
    """Runs every step of a plan. Returns (all_ok, log_lines)."""
    log: list[str] = []

    def emit(line: str):
        log.append(line)
        if on_line:
            on_line(line)

    ok = True

    if plan.needs_i386 or plan.packages:
        req = {"action": "apt_install", "packages": plan.packages, "label": "Selected components"}
        emit(f"Requesting admin rights to install: {', '.join(plan.packages) or '(arch only)'}")
        result = run_privileged_streaming(req, emit)
        if not result.ok:
            emit(f"FAILED: {result.error}")
            ok = False

    for action in plan.privileged_actions:
        emit(f"Requesting admin rights for: {action.get('label')}")
        result = run_privileged_streaming(action, emit)
        if not result.ok:
            emit(f"FAILED: {result.error}")
            ok = False

    for component in plan.unprivileged:
        emit(f"Applying: {component.name}")
        try:
            apply_unprivileged(component, wine_prefix, emit)
        except Exception as e:  # noqa: BLE001
            emit(f"FAILED: {component.name}: {e}")
            ok = False

    return ok, log


# ---------------------------------------------------------------------------
# Unprivileged handlers
# ---------------------------------------------------------------------------

def _default_prefix(wine_prefix: str | None) -> Path:
    return Path(wine_prefix or os.environ.get("WINEPREFIX", str(Path.home() / ".wine")))


def _latest_release_asset(repo: str, asset_re: str) -> tuple[str, str]:
    req = urllib.request.Request(GITHUB_API.format(repo=repo), headers={"User-Agent": "griffin-persona"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read())
    for asset in data.get("assets", []):
        if re.match(asset_re, asset["name"]):
            return asset["name"], asset["browser_download_url"]
    raise RuntimeError(f"No matching release asset on {repo}")


def _download(url: str, dest: Path, on_line) -> None:
    on_line(f"Downloading {url}")
    urllib.request.urlretrieve(url, dest)


def apply_unprivileged(component: Component, wine_prefix: str | None, on_line) -> None:
    action = component.user_action or ""

    if action == "install_wine_ge":
        name, url = _latest_release_asset("GloriousEggroll/wine-ge-custom", r".*\.tar\.xz$")
        dest_dir = Path.home() / ".local" / "share" / "lutris" / "runners" / "wine"
        dest_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / name
            _download(url, archive, on_line)
            subprocess.run(["tar", "-xJf", str(archive), "-C", str(dest_dir)], check=True,
                           stdin=subprocess.DEVNULL, timeout=300)
        on_line(f"Installed {name} to {dest_dir}")

    elif action == "install_proton_ge":
        name, url = _latest_release_asset("GloriousEggroll/proton-ge-custom", r".*\.tar\.gz$")
        dest_dir = Path.home() / ".steam" / "root" / "compatibilitytools.d"
        dest_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / name
            _download(url, archive, on_line)
            subprocess.run(["tar", "-xzf", str(archive), "-C", str(dest_dir)], check=True,
                           stdin=subprocess.DEVNULL, timeout=300)
        on_line(f"Installed {name} to {dest_dir} — restart Steam to see it under Compatibility tools.")

    elif action == "verify_proton_experimental":
        protons = detect.proton_installations()
        if any("experimental" in p.lower() for p in protons):
            on_line("Proton Experimental found.")
        else:
            on_line("Proton Experimental not found — install/update it from Steam > Tools.")

    elif action == "install_dxvk":
        name, url = _latest_release_asset("doitsujin/dxvk", r".*\.tar\.gz$")
        prefix = _default_prefix(wine_prefix)
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / name
            _download(url, archive, on_line)
            subprocess.run(["tar", "-xzf", str(archive), "-C", tmp], check=True,
                           stdin=subprocess.DEVNULL, timeout=300)
            extracted = next(Path(tmp).glob("dxvk-*/"))
            setup = extracted / "setup_dxvk.sh"
            env = {**os.environ, "WINEPREFIX": str(prefix)}
            subprocess.run(["bash", str(setup), "install", "--symlink"], check=True, env=env,
                           stdin=subprocess.DEVNULL, timeout=300)
        on_line(f"DXVK installed into {prefix}")

    elif action.startswith("winetricks:"):
        verb = action.split(":", 1)[1]
        prefix = _default_prefix(wine_prefix)
        if not shutil.which("winetricks"):
            raise RuntimeError("winetricks is not installed — add it from Windows Compatibility > Core first.")
        env = {**os.environ, "WINEPREFIX": str(prefix)}
        on_line(f"Running winetricks -q {verb} in {prefix}")
        subprocess.run(["winetricks", "-q", verb], check=True, env=env,
                       stdin=subprocess.DEVNULL, timeout=600)

    elif action.startswith("flatpak:"):
        app_id = action.split(":", 1)[1]
        if not shutil.which("flatpak"):
            raise RuntimeError("Flatpak is not installed — enable it from General first.")
        subprocess.run(["flatpak", "remote-add", "--user", "--if-not-exists",
                         "flathub", "https://flathub.org/repo/flathub.flatpakrepo"], check=False,
                       stdin=subprocess.DEVNULL, timeout=60)
        on_line(f"Installing {app_id} from Flathub (user install, no admin needed)")
        subprocess.run(["flatpak", "install", "--user", "-y", "flathub", app_id], check=True,
                       stdin=subprocess.DEVNULL, timeout=900)

    elif action == "apply_audio_latency_preset":
        conf_dir = Path.home() / ".config" / "pipewire" / "pipewire.conf.d"
        conf_dir.mkdir(parents=True, exist_ok=True)
        (conf_dir / "99-griffin-gaming-latency.conf").write_text(
            "context.properties = {\n"
            "    default.clock.rate = 48000\n"
            "    default.clock.quantum = 256\n"
            "    default.clock.min-quantum = 256\n"
            "}\n"
        )
        on_line("Applied low-latency PipeWire preset. Log out/in (or restart pipewire) to take effect.")

    elif action == "export_profile_backup":
        history = state.read_history()
        dest = Path.home() / "griffin-persona-backup.json"
        dest.write_text(json.dumps(history, indent=2))
        on_line(f"Exported profile history to {dest}")

    elif action.startswith("repair:reset_prefix"):
        prefix = _default_prefix(wine_prefix)
        if prefix.exists():
            shutil.rmtree(prefix)
        env = {**os.environ, "WINEPREFIX": str(prefix)}
        subprocess.run(["wineboot", "-u"], check=True, env=env, stdin=subprocess.DEVNULL, timeout=120)
        on_line(f"Recreated wine prefix at {prefix}")

    else:
        on_line(f"No handler for action '{action}' yet — skipped.")
