"""Gaming layer page — overlays, RGB control, capture/streaming, controllers, retro & emulation."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from .. import actions, anticheat
from ..packages import GAMING_COMPONENTS, RETRO_EMULATION_COMPONENTS
from ..widgets import ComponentGroup, confirm_and_apply, section_subtitle, section_title


class GamingPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(section_title("Gaming"))
        layout.addWidget(section_subtitle(
            "Performance overlays, RGB control, capture and streaming tools."
        ))

        self.group = ComponentGroup("Gaming Tools", GAMING_COMPONENTS)
        layout.addWidget(self.group)

        apply_row = QHBoxLayout()
        apply_row.addStretch()
        apply_btn = QPushButton("Preview && Apply")
        apply_btn.setObjectName("Primary")
        apply_btn.clicked.connect(self._apply)
        apply_row.addWidget(apply_btn)
        layout.addLayout(apply_row)

        retro_note = QLabel(
            "Every entry below installs via Flatpak, and needs Flatpak enabled first — "
            "the toggle for that lives on the General page."
        )
        retro_note.setObjectName("Muted")
        retro_note.setWordWrap(True)
        layout.addWidget(retro_note)

        self.retro_group = ComponentGroup("Retro & Emulation", RETRO_EMULATION_COMPONENTS)
        layout.addWidget(self.retro_group)

        retro_apply_row = QHBoxLayout()
        retro_apply_row.addStretch()
        retro_apply_btn = QPushButton("Preview && Apply")
        retro_apply_btn.setObjectName("Primary")
        retro_apply_btn.clicked.connect(self._apply_retro)
        retro_apply_row.addWidget(retro_apply_btn)
        layout.addLayout(retro_apply_row)

        layout.addWidget(self._build_anticheat_checker())
        layout.addStretch()

    def _apply(self):
        plan = actions.build_plan(self.group.selected_components())
        confirm_and_apply(self, plan)

    def _apply_retro(self):
        plan = actions.build_plan(self.retro_group.selected_components())
        confirm_and_apply(self, plan)

    def _build_anticheat_checker(self) -> QWidget:
        box = QWidget()
        box.setObjectName("Card")
        layout = QVBoxLayout(box)

        header = QLabel("Anti-Cheat Compatibility Checker")
        header.setObjectName("SectionHeader")
        layout.addWidget(header)

        note = QLabel(
            "Informational only, sourced from the community-maintained AreWeAntiCheatYet "
            "project — this never installs, patches, or configures an anti-cheat. It just "
            "tells you what's currently known."
        )
        note.setObjectName("Muted")
        note.setWordWrap(True)
        layout.addWidget(note)

        search_row = QHBoxLayout()
        self.ac_input = QLineEdit()
        self.ac_input.setPlaceholderText("Search a game title…")
        self.ac_input.returnPressed.connect(self._run_anticheat_search)
        search_row.addWidget(self.ac_input, 1)
        search_btn = QPushButton("Check")
        search_btn.clicked.connect(self._run_anticheat_search)
        search_row.addWidget(search_btn)
        layout.addLayout(search_row)

        self.ac_results_layout = QVBoxLayout()
        layout.addLayout(self.ac_results_layout)

        self.ac_status_label = QLabel(anticheat.cache_age_description())
        self.ac_status_label.setObjectName("Muted")
        layout.addWidget(self.ac_status_label)

        return box

    def _run_anticheat_search(self):
        for i in reversed(range(self.ac_results_layout.count())):
            item = self.ac_results_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()

        query = self.ac_input.text().strip()
        if not query:
            return

        try:
            results = anticheat.search(query)
        except Exception as e:  # noqa: BLE001 - network/parse failures shouldn't crash the page
            err = QLabel(f"Couldn't reach the compatibility data source: {e}")
            err.setObjectName("StatusWarn")
            self.ac_results_layout.addWidget(err)
            return

        self.ac_status_label.setText(anticheat.cache_age_description())

        if not results:
            self.ac_results_layout.addWidget(QLabel("No match found in the compatibility list."))
            return

        status_obj = {"supported": "StatusOk", "running": "StatusOk", "denied": "StatusBad", "broken": "StatusBad"}
        for r in results:
            row = QHBoxLayout()
            status_lbl = QLabel(f"{r.status}")
            status_lbl.setObjectName(status_obj.get(r.status.lower(), "StatusWarn"))
            status_lbl.setFixedWidth(90)
            row.addWidget(status_lbl)
            text = r.name
            if r.anticheats:
                text += f"  ({', '.join(r.anticheats)})"
            name_lbl = QLabel(text)
            name_lbl.setWordWrap(True)
            row.addWidget(name_lbl, 1)
            container = QWidget()
            container.setLayout(row)
            self.ac_results_layout.addWidget(container)
