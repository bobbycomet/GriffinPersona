"""
Griffin Persona — application state helpers.

Two separate state areas are used, deliberately:

1. ~/.config/autostart/griffin-persona-firstrun.desktop
   A per-user override of the system-wide autostart entry shipped at
   /etc/xdg/autostart/griffin-persona-firstrun.desktop. Writing a
   ``Hidden=true`` override here is the standard XDG mechanism for a user
   session to suppress an autostart entry, and it requires no special
   privilege. This is how Griffin Persona stops launching itself on every
   boot after the welcome flow has been seen once, while remaining a normal,
   ordinary app reachable from the application menu afterwards.

2. /var/lib/griffin-postinstall/
   System-level state: hardware-detection cache, the udev "topology changed"
   flag, and the package/profile rollback ledger. This directory is created
   by the .deb postinst script and is written to exclusively by the
   privileged helper (running as root via polkit). The GUI only ever reads
   from it.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

AUTOSTART_DESKTOP_ID = "griffin-persona-firstrun.desktop"
SYSTEM_STATE_DIR = Path("/var/lib/griffin-postinstall")
HISTORY_FILE = SYSTEM_STATE_DIR / "history.json"
HW_CHANGED_FLAG = SYSTEM_STATE_DIR / "hw-changed"
DIAGNOSTICS_SNAPSHOT = SYSTEM_STATE_DIR / "last-diagnostics.json"


def user_config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base)


def user_autostart_dir() -> Path:
    d = user_config_dir() / "autostart"
    d.mkdir(parents=True, exist_ok=True)
    return d


def has_seen_welcome() -> bool:
    """True once this user has dismissed/completed the welcome flow."""
    override = user_autostart_dir() / AUTOSTART_DESKTOP_ID
    if override.exists():
        return True
    marker = user_config_dir() / "griffin-persona" / "welcomed"
    return marker.exists()


def mark_welcome_seen() -> None:
    """Suppress the autostart entry for this user and drop a local marker."""
    override = user_autostart_dir() / AUTOSTART_DESKTOP_ID
    override.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Hidden=true\n"
    )
    marker_dir = user_config_dir() / "griffin-persona"
    marker_dir.mkdir(parents=True, exist_ok=True)
    (marker_dir / "welcomed").write_text("1")


def hw_topology_changed() -> bool:
    return HW_CHANGED_FLAG.exists()


def clear_hw_topology_flag_request() -> dict:
    """Returns the helper request needed to clear the udev flag (root-owned)."""
    return {"action": "clear_hw_flag"}


def read_history() -> list:
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def read_diagnostics_snapshot() -> dict | None:
    if not DIAGNOSTICS_SNAPSHOT.exists():
        return None
    try:
        return json.loads(DIAGNOSTICS_SNAPSHOT.read_text())
    except (json.JSONDecodeError, OSError):
        return None
