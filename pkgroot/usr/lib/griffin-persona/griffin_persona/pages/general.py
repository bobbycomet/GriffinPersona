"""General persona page — browsers and everyday apps, for anyone who just wants a good default desktop."""

from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from .. import actions
from ..packages import GENERAL_COMPONENTS
from ..widgets import ComponentGroup, confirm_and_apply, section_subtitle, section_title


class GeneralPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(section_title("General"))
        layout.addWidget(section_subtitle(
            "Browsers and everyday apps for anyone who doesn't have a specific gaming, "
            "creative, or development workflow in mind — or who just wants these regardless. "
            "Every browser here is a genuinely native package: Falkon comes straight from "
            "the standard repos, and Firefox is installed from Mozilla's official "
            "repository specifically so you get the real package, not a Snap in disguise. "
            "Flatpak and Snap support also live here, since several entries elsewhere in "
            "this app (Retro & Emulation in particular) install through Flatpak."
        ))

        self.group = ComponentGroup("General Apps", GENERAL_COMPONENTS)
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
