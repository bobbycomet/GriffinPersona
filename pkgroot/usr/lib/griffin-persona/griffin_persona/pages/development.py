"""Development layer page — for people switching from Windows who also code."""

from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from .. import actions
from ..packages import DEV_COMPONENTS
from ..widgets import ComponentGroup, confirm_and_apply, section_subtitle, section_title


class DevelopmentPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(section_title("Development"))
        layout.addWidget(section_subtitle(
            "Optional — the basics for building software on Griffin Linux."
        ))

        self.group = ComponentGroup("Development Tools", DEV_COMPONENTS)
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
