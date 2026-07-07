"""Storage & Reliability page — snapshots, firmware, backup export."""

from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .. import actions, detect
from ..packages import STORAGE_COMPONENTS
from ..widgets import ComponentGroup, confirm_and_apply, section_subtitle, section_title


class StoragePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(section_title("Storage & Reliability"))
        layout.addWidget(section_subtitle(
            "The boring stuff that prevents support tickets: snapshots and firmware updates. "
            "Flatpak and Snap support moved to the General page."
        ))

        if not detect.is_btrfs_root():
            note = QLabel("Note: your root filesystem isn't btrfs, so BTRFS Assistant won't have much to manage.")
            note.setObjectName("Muted")
            layout.addWidget(note)

        self.group = ComponentGroup("Storage Tools", STORAGE_COMPONENTS)
        layout.addWidget(self.group)

        apply_row = QHBoxLayout()
        apply_row.addStretch()
        apply_btn = QPushButton("Preview && Apply")
        apply_btn.setObjectName("Primary")
        apply_btn.clicked.connect(self._apply)
        apply_row.addWidget(apply_btn)
        layout.addLayout(apply_row)
        layout.addStretch()

    def _apply(self):
        plan = actions.build_plan(self.group.selected_components())
        confirm_and_apply(self, plan)
