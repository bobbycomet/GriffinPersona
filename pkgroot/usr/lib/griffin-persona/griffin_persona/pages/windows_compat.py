"""Windows Compatibility page."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QTabWidget,
    QVBoxLayout, QWidget,
)

from .. import actions, detect
from ..packages import (
    WIN_CORE, WIN_LAUNCHERS, WIN_REPAIR_ACTIONS, WIN_RUNNERS,
    WIN_RUNTIME_OPTIONAL, WIN_RUNTIME_RECOMMENDED,
)
from ..widgets import ComponentGroup, confirm_and_apply, section_subtitle, section_title


class WindowsCompatPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(section_title("Windows Compatibility"))
        layout.addWidget(section_subtitle(
            "Wine, Proton and everything around them — built up in layers so you only "
            "add what a given game actually needs. A lot of prefix instability comes "
            "from piling on every Winetricks component 'just in case', so Optional "
            "items here stay unchecked by default."
        ))

        prefix_row = QHBoxLayout()
        prefix_row.addWidget(QLabel("Wine prefix for runtime-library actions:"))
        self.prefix_edit = QLineEdit(str(detect.wine_prefix_health()["path"]))
        prefix_row.addWidget(self.prefix_edit, 1)
        layout.addLayout(prefix_row)

        tabs = QTabWidget()

        self.core_group = ComponentGroup("Core", WIN_CORE)
        tabs.addTab(self._wrap_with_apply(self.core_group), "Core")

        self.runners_group = ComponentGroup("Runners", WIN_RUNNERS)
        tabs.addTab(self._wrap_with_apply(self.runners_group), "Runners")

        runtime_widget = QWidget()
        runtime_layout = QVBoxLayout(runtime_widget)
        self.runtime_recommended = ComponentGroup("Recommended", WIN_RUNTIME_RECOMMENDED)
        self.runtime_optional = ComponentGroup("Optional", WIN_RUNTIME_OPTIONAL)
        runtime_layout.addWidget(self.runtime_recommended)
        runtime_layout.addWidget(self.runtime_optional)
        runtime_layout.addWidget(self._apply_row(lambda: self.runtime_recommended.selected_components()
                                                  + self.runtime_optional.selected_components()))
        tabs.addTab(runtime_widget, "Runtime Libraries")

        self.launchers_group = ComponentGroup("Launchers", WIN_LAUNCHERS)
        tabs.addTab(self._wrap_with_apply(self.launchers_group), "Launchers")

        repair_widget = QWidget()
        repair_layout = QVBoxLayout(repair_widget)
        repair_layout.addWidget(QLabel(
            "Repair actions act on the prefix above and never touch other prefixes."
        ))
        for label in WIN_REPAIR_ACTIONS:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, lbl=label: self._run_repair(lbl))
            repair_layout.addWidget(btn)
        self.repair_output = QPlainTextEdit()
        self.repair_output.setReadOnly(True)
        repair_layout.addWidget(self.repair_output)
        tabs.addTab(repair_widget, "Repair")

        layout.addWidget(tabs)

    def _wrap_with_apply(self, group: ComponentGroup) -> QWidget:
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.addWidget(group)
        wrapper_layout.addWidget(self._apply_row(group.selected_components))
        return wrapper

    def _apply_row(self, get_selected) -> QWidget:
        row = QWidget()
        h = QHBoxLayout(row)
        h.addStretch()
        btn = QPushButton("Preview && Apply")
        btn.setObjectName("Primary")
        btn.clicked.connect(lambda: confirm_and_apply(
            self, actions.build_plan(get_selected()), wine_prefix=self.prefix_edit.text()
        ))
        h.addWidget(btn)
        return row

    def _run_repair(self, label: str):
        prefix = self.prefix_edit.text()
        if label == "Reset prefix":
            from ..packages import Component
            plan = actions.build_plan([Component("repair_reset", "Reset prefix", "", user_action="repair:reset_prefix")])
            confirm_and_apply(self, plan, wine_prefix=prefix)
        elif label == "Verify Vulkan":
            vk = detect.vulkan_status()
            self.repair_output.appendPlainText(f"Vulkan 64-bit: {vk['vulkan']} | 32-bit: {vk['vulkan_i386']}")
        elif label == "Rebuild symlinks":
            import os
            import subprocess
            env = {**os.environ, "WINEPREFIX": prefix}
            try:
                subprocess.run(["wineboot", "-u"], check=True, env=env, timeout=120, stdin=subprocess.DEVNULL)
                self.repair_output.appendPlainText("wineboot -u completed (symlinks/registry rebuilt).")
            except Exception as e:  # noqa: BLE001
                self.repair_output.appendPlainText(f"Failed: {e}")
        elif label == "Dependency diagnostics":
            wine = detect.wine_status()
            health = detect.wine_prefix_health(prefix)
            vcrun = detect.vc_runtime_hint(prefix)
            self.repair_output.appendPlainText(
                f"Wine: {wine['installed']} ({wine['version']}) | "
                f"Prefix healthy: {health['healthy']} | VC runtime present: {vcrun}"
            )
