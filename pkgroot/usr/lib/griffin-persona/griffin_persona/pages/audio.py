"""Audio page — PipeWire-centric stack with a health check section."""

from __future__ import annotations

import subprocess

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .. import actions, detect
from ..packages import AUDIO_COMPONENTS
from ..widgets import ComponentGroup, confirm_and_apply, section_subtitle, section_title


class AudioPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(section_title("Audio"))
        layout.addWidget(section_subtitle(
            "PipeWire stack components, treated the same way as everything else here: "
            "pick what you want, preview it, apply it."
        ))

        self.group = ComponentGroup("PipeWire Stack", AUDIO_COMPONENTS)
        layout.addWidget(self.group)

        apply_row = QHBoxLayout()
        apply_row.addStretch()
        apply_btn = QPushButton("Preview && Apply")
        apply_btn.setObjectName("Primary")
        apply_btn.clicked.connect(self._apply)
        apply_row.addWidget(apply_btn)
        layout.addLayout(apply_row)

        layout.addWidget(QLabel("Health Check"))
        self.health_labels: dict[str, QLabel] = {}
        health_row = QHBoxLayout()
        for name in ["Mic", "Output", "JACK", "Bluetooth", "Sample Rate"]:
            lbl = QLabel(f"○ {name}")
            self.health_labels[name] = lbl
            health_row.addWidget(lbl)
        layout.addLayout(health_row)

        run_health_btn = QPushButton("Run Health Check")
        run_health_btn.clicked.connect(self._run_health_check)
        layout.addWidget(run_health_btn)

        layout.addStretch()

    def _apply(self):
        plan = actions.build_plan(self.group.selected_components())
        confirm_and_apply(self, plan)

    def _set_status(self, name: str, ok: bool | None):
        symbol = "✓" if ok else ("✗" if ok is False else "○")
        obj = "StatusOk" if ok else ("StatusBad" if ok is False else "Muted")
        lbl = self.health_labels[name]
        lbl.setText(f"{symbol} {name}")
        lbl.setObjectName(obj)
        lbl.setStyleSheet("")

    def _probe(self, cmd: list[str], timeout: int = 5) -> "subprocess.CompletedProcess | None":
        """
        Best-effort probe used only for health-check status, never for
        anything that changes the system. Always redirects stdin to
        /dev/null — without that, a command like `bluetoothctl show` can
        inherit the real terminal's stdin when this app is run with
        `python3 run.py` from a shell, drop into its own interactive
        prompt waiting for input, and hang for the full timeout on every
        single health check. Catches everything (missing binary, timeout,
        permission errors) because a probe failing should just show as
        "unknown" on the health row, never crash or freeze the page.
        """
        try:
            return subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL,
            )
        except Exception:  # noqa: BLE001 - any failure here just means "unknown", not a crash
            return None

    def _run_health_check(self):
        pw = detect.pipewire_status()
        self._set_status("Output", pw["pipewire"])
        self._set_status("JACK", detect.which("pw-jack") or detect.is_package_installed("pipewire-jack"))

        p = self._probe(["pactl", "list", "short", "sources"])
        mic_ok = (p.returncode == 0 and bool(p.stdout.strip())) if p else None
        self._set_status("Mic", mic_ok)

        p = self._probe(["bluetoothctl", "show"])
        bt_ok = ("Powered: yes" in p.stdout) if p else None
        self._set_status("Bluetooth", bt_ok)

        p = self._probe(["pw-metadata", "-n", "settings"])
        rate_ok = ("clock.rate" in p.stdout) if p else None
        self._set_status("Sample Rate", rate_ok)
