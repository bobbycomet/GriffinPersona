"""Creative persona page — video, audio, image, and 3D tools."""

from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from .. import actions
from ..packages import CREATIVE_COMPONENTS
from ..widgets import ComponentGroup, confirm_and_apply, section_subtitle, section_title


class CreativePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(section_title("Creative"))
        layout.addWidget(section_subtitle(
            "Recording, video editing, image editing, and 3D — the toolkit for a "
            "content-creation persona. OBS also appears on the Gaming page; picking it from "
            "either one installs the same thing."
        ))

        self.group = ComponentGroup("Creative Tools", CREATIVE_COMPONENTS)
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
