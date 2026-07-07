"""GPU & Drivers page — profiles, not blanket driver installs."""

from __future__ import annotations

import subprocess

from PyQt6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit, QPushButton,
    QTabWidget, QVBoxLayout, QWidget,
)

from .. import detect, state
from ..packages import GPU_PROFILES, NVIDIA_LAPTOP_COMPONENTS
from ..widgets import ComponentGroup, confirm_and_apply, section_subtitle, section_title


class GpuDriversPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(section_title("GPU & Drivers"))
        layout.addWidget(section_subtitle(
            "Hardware detection selects a profile for you to review — it never installs "
            "a driver on its own. Pick the components you want, preview exactly what "
            "will change, then apply."
        ))

        gpus = detect.detect_gpus()
        vendors = sorted({g.vendor for g in gpus if g.vendor != "unknown"}) or ["nvidia", "amd", "intel"]
        detected_line = ", ".join(f"{g.name} ({g.vendor})" for g in gpus) or "No GPU detected via lspci"
        layout.addWidget(QLabel(f"Detected: {detected_line}"))

        layout.addWidget(self._build_device_type_row())

        autotune_panel = self._build_autotune_panel()
        if autotune_panel:
            layout.addWidget(autotune_panel)

        if state.hw_topology_changed():
            warn = QLabel("⚠ Hardware topology changed since the last check (e.g. GPU hot-plug) — re-detection recommended.")
            warn.setObjectName("StatusWarn")
            layout.addWidget(warn)

        self.tabs = QTabWidget()
        self.groups: dict[str, ComponentGroup] = {}
        for vendor, components in GPU_PROFILES.items():
            group = ComponentGroup(vendor.upper(), components)
            self.groups[vendor] = group
            self.tabs.addTab(group, vendor.upper())
        # Pre-select the tab matching detected hardware.
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i).lower() in vendors:
                self.tabs.setCurrentIndex(i)
                break
        layout.addWidget(self.tabs)

        button_row = QHBoxLayout()
        recommended_btn = QPushButton("Select Recommended")
        recommended_btn.clicked.connect(self._select_recommended)
        all_btn = QPushButton("Install All (this vendor)")
        all_btn.clicked.connect(self._select_all)
        none_btn = QPushButton("Clear")
        none_btn.clicked.connect(self._select_none)
        preview_btn = QPushButton("Preview && Apply")
        preview_btn.setObjectName("Primary")
        preview_btn.clicked.connect(self._preview_apply)
        button_row.addWidget(recommended_btn)
        button_row.addWidget(all_btn)
        button_row.addWidget(none_btn)
        button_row.addStretch()
        button_row.addWidget(preview_btn)
        layout.addLayout(button_row)

        layout.addWidget(QLabel(
            "Mixing components across vendor tabs (e.g. NVIDIA driver + a generic tool) "
            "is fine — apply each tab separately and they combine into your own custom setup."
        ))

        hybrid_section = self._build_hybrid_section()
        if hybrid_section:
            layout.addWidget(hybrid_section)

        action_row = QHBoxLayout()
        for label, handler in [
            ("Validate Driver", self._validate_driver),
            ("Validate Vulkan", self._validate_vulkan),
            ("Benchmark", self._benchmark),
            ("Repair", self._repair),
            ("Rollback", self._rollback),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            action_row.addWidget(btn)
        self.install_vkmark_btn = QPushButton("Install vkmark")
        self.install_vkmark_btn.setVisible(not detect.which("vkmark"))
        self.install_vkmark_btn.clicked.connect(self._install_vkmark)
        action_row.addWidget(self.install_vkmark_btn)
        layout.addLayout(action_row)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumHeight(140)
        layout.addWidget(self.output)

    def _build_device_type_row(self) -> QWidget:
        info = detect.device_type()
        source_note = (
            "from Kernel Auto-tune" if info["source"] == "kernel-autotune" else "auto-detected"
        )
        label = QLabel(f"Device type: {info['type'].capitalize()} ({source_note})")
        label.setObjectName("Muted")
        return label

    def _build_autotune_panel(self) -> QWidget | None:
        """
        Shows what Kernel Auto-tune already knows about this machine, when
        its state.json is present. Purely informational — this never feeds
        back into what driver gets installed; it exists so the person can
        see the system already knows their actual hardware, not a generic
        guess. Returns None (and the caller skips it) when the file isn't
        there, e.g. Kernel Auto-tune hasn't run yet or isn't installed.
        """
        autotune_state = detect.read_kernel_autotune_state()
        if not autotune_state:
            return None

        box = QWidget()
        box.setObjectName("Card")
        layout = QVBoxLayout(box)
        header = QLabel("Kernel Auto-tune already knows this machine")
        header.setObjectName("SectionHeader")
        layout.addWidget(header)

        fields = [
            ("Host", autotune_state.get("hostname")),
            ("Distro", autotune_state.get("distro")),
            ("Kernel", autotune_state.get("kernel_version") or autotune_state.get("kernel")),
            ("CPU", autotune_state.get("cpu_model")),
            ("GPU", autotune_state.get("gpu_model")),
            ("GPU driver", autotune_state.get("gpu_driver")),
            ("Last tuned", autotune_state.get("last_updated")),
        ]
        summary = "  •  ".join(f"{k}: {v}" for k, v in fields if v)
        if summary:
            summary_label = QLabel(summary)
            summary_label.setWordWrap(True)
            layout.addWidget(summary_label)
        return box

    def _build_hybrid_section(self) -> QWidget | None:
        """
        Only shown when more than one GPU vendor is actually present
        (typically an Intel or AMD integrated GPU alongside an NVIDIA
        discrete one) or Kernel Auto-tune's own state.json says this is a
        laptop with an NVIDIA card — the PRIME/Optimus components below are
        meaningless noise on a single-GPU desktop, so they don't show up as
        one there at all rather than being shown disabled or unchecked.
        """
        vendors = set(detect.primary_gpu_vendors())
        autotune_state = detect.read_kernel_autotune_state() or {}
        looks_like_nvidia_laptop = (
            detect.device_type()["type"] == "laptop"
            and ("nvidia" in vendors or "nvidia" in str(autotune_state.get("gpu_model", "")).lower())
        )
        if not (detect.is_hybrid_graphics() or looks_like_nvidia_laptop):
            return None

        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        note = QLabel(
            "Laptop / hybrid graphics detected — these handle switching between your "
            "integrated and discrete GPUs, on top of the driver above."
        )
        note.setObjectName("Muted")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.hybrid_group = ComponentGroup("Laptop / Hybrid Graphics", NVIDIA_LAPTOP_COMPONENTS)
        layout.addWidget(self.hybrid_group)

        apply_row = QHBoxLayout()
        apply_row.addStretch()
        apply_btn = QPushButton("Preview && Apply")
        apply_btn.clicked.connect(self._apply_hybrid)
        apply_row.addWidget(apply_btn)
        layout.addLayout(apply_row)
        return box

    def _apply_hybrid(self):
        from .. import actions
        plan = actions.build_plan(self.hybrid_group.selected_components())
        confirm_and_apply(self, plan)

    def _current_group(self) -> ComponentGroup:
        return self.tabs.currentWidget()

    def _select_recommended(self):
        self._current_group().select_recommended_only()

    def _select_all(self):
        self._current_group().select_all()

    def _select_none(self):
        self._current_group().select_none()

    def _preview_apply(self):
        from .. import actions
        selected = self._current_group().selected_components()
        plan = actions.build_plan(selected)
        confirm_and_apply(self, plan)

    def _log(self, text: str):
        self.output.appendPlainText(text)

    def _validate_driver(self):
        vendor = self.tabs.tabText(self.tabs.currentIndex()).lower()
        summary = detect.gpu_driver_summary(vendor)
        self._log(f"[{vendor.upper()}] driver present: {summary['driver_present']} — {summary['detail']}")

    def _validate_vulkan(self):
        vk = detect.vulkan_status()
        self._log(f"Vulkan 64-bit: {vk['vulkan']} | Vulkan 32-bit: {vk['vulkan_i386']} | {vk['detail']}")

    def _benchmark(self):
        if detect.which("vkmark"):
            self._log("Running vkmark (this can take a moment)…")
            try:
                p = subprocess.run(["vkmark", "--duration", "3"], capture_output=True, text=True,
                                    timeout=30, stdin=subprocess.DEVNULL)
                self._log(p.stdout.strip().splitlines()[-1] if p.stdout.strip() else "vkmark produced no output")
            except Exception as e:  # noqa: BLE001
                self._log(f"vkmark failed: {e}")
        else:
            self._log("vkmark isn't installed — use the 'Install vkmark' button to add it.")

    def _install_vkmark(self):
        from .. import actions
        from ..packages import VKMARK_COMPONENT
        plan = actions.build_plan([VKMARK_COMPONENT])
        confirm_and_apply(self, plan)
        self.install_vkmark_btn.setVisible(not detect.which("vkmark"))

    def _repair(self):
        vendor = self.tabs.tabText(self.tabs.currentIndex()).lower()
        from .. import actions
        plan = actions.build_plan(GPU_PROFILES.get(vendor, []))
        confirm_and_apply(self, plan)

    def _rollback(self):
        history = state.read_history()
        if not history:
            QMessageBox.information(self, "Rollback", "No recorded changes to roll back yet.")
            return
        combo = QComboBox()
        for i, entry in enumerate(history):
            combo.addItem(f"{i}: {entry.get('label') or entry.get('action')} ({entry.get('timestamp', '')[:19]})")
        box = QMessageBox(self)
        box.setWindowTitle("Rollback")
        box.setText("Pick a recorded change to undo:")
        box.layout().addWidget(combo, 1, 0, 1, box.layout().columnCount())
        box.setStandardButtons(QMessageBox.StandardButton.Cancel)
        undo_btn = box.addButton("Undo", QMessageBox.ButtonRole.AcceptRole)
        box.exec()
        if box.clickedButton() == undo_btn:
            from ..privileged import run_privileged
            index = combo.currentIndex()
            result = run_privileged({"action": "rollback", "history_index": index})
            self._log(result.log or result.error)
