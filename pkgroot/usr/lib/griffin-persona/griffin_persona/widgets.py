"""
Griffin Persona — shared widgets.

The "detect -> select profile -> preview -> apply" pattern used by every
component-driven page (GPU, Windows Compatibility, Audio, Gaming, Storage,
Development) lives here once, instead of being re-implemented per page.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QGroupBox, QHBoxLayout, QLabel,
    QPlainTextEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from . import actions


class ComponentRow(QWidget):
    def __init__(self, component, parent=None):
        super().__init__(parent)
        self.component = component
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(component.recommended)
        layout.addWidget(self.checkbox)

        text_box = QVBoxLayout()
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        name_label = QLabel(component.name)
        name_label.setStyleSheet("font-weight: 600;")
        title_row.addWidget(name_label)
        badge = QLabel("RECOMMENDED" if component.recommended else "OPTIONAL")
        badge.setObjectName("Badge" if component.recommended else "BadgeOptional")
        title_row.addWidget(badge)
        title_row.addStretch()
        text_box.addLayout(title_row)

        desc = QLabel(component.description)
        desc.setObjectName("Muted")
        desc.setWordWrap(True)
        text_box.addWidget(desc)

        layout.addLayout(text_box, stretch=1)

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()


class ComponentGroup(QGroupBox):
    """A titled group of ComponentRows, e.g. 'Runners' or 'NVIDIA'."""

    def __init__(self, title: str, components, parent=None):
        super().__init__(title, parent)
        self.rows: list[ComponentRow] = []
        layout = QVBoxLayout(self)
        for c in components:
            row = ComponentRow(c)
            self.rows.append(row)
            layout.addWidget(row)

    def selected_components(self):
        return [r.component for r in self.rows if r.is_checked()]

    def select_recommended_only(self):
        for r in self.rows:
            r.checkbox.setChecked(r.component.recommended)

    def select_all(self):
        for r in self.rows:
            r.checkbox.setChecked(True)

    def select_none(self):
        for r in self.rows:
            r.checkbox.setChecked(False)


class ApplyWorker(QThread):
    line = pyqtSignal(str)
    finished_ok = pyqtSignal(bool)

    def __init__(self, plan, wine_prefix: str | None = None, parent=None):
        super().__init__(parent)
        self.plan = plan
        self.wine_prefix = wine_prefix

    def run(self):
        ok, _ = actions.apply_plan(self.plan, on_line=self.line.emit, wine_prefix=self.wine_prefix)
        self.finished_ok.emit(ok)


class ApplyLogDialog(QDialog):
    """Modal-ish progress window showing live output while a plan is applied."""

    def __init__(self, plan, wine_prefix: str | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Applying changes")
        self.setMinimumSize(560, 420)
        layout = QVBoxLayout(self)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)

        self.status_label = QLabel("Working…")
        layout.addWidget(self.status_label)

        self.close_button = QPushButton("Close")
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button)

        self.worker = ApplyWorker(plan, wine_prefix)
        self.worker.line.connect(self._append)
        self.worker.finished_ok.connect(self._finished)

    def start(self):
        self.worker.start()

    def _append(self, text: str):
        self.log_view.appendPlainText(text)

    def _finished(self, ok: bool):
        self.status_label.setText("Done." if ok else "Finished with errors — see log above.")
        self.status_label.setObjectName("StatusOk" if ok else "StatusBad")
        self.status_label.setStyleSheet("")  # re-apply via objectName
        self.close_button.setEnabled(True)


def confirm_and_apply(parent, plan, wine_prefix: str | None = None) -> None:
    """Show the 'here is exactly what will change' preview, then apply on confirm."""
    preview = actions.describe_plan(plan)
    dlg = QDialog(parent)
    dlg.setWindowTitle("Preview changes")
    dlg.setMinimumWidth(480)
    layout = QVBoxLayout(dlg)
    layout.addWidget(QLabel("The following will change:"))
    body = QPlainTextEdit(preview)
    body.setReadOnly(True)
    layout.addWidget(body)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
    apply_btn = QPushButton("Apply")
    apply_btn.setObjectName("Primary")
    buttons.addButton(apply_btn, QDialogButtonBox.ButtonRole.AcceptRole)
    buttons.rejected.connect(dlg.reject)
    buttons.accepted.connect(dlg.accept)
    layout.addWidget(buttons)

    if not preview.strip() or preview.strip() == "Nothing selected.":
        body.setPlainText("Nothing selected — tick at least one component first.")
        apply_btn.setEnabled(False)

    if dlg.exec() == QDialog.DialogCode.Accepted:
        log_dlg = ApplyLogDialog(plan, wine_prefix, parent)
        log_dlg.start()
        log_dlg.exec()


def section_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("PageTitle")
    return label


def section_subtitle(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("PageSubtitle")
    label.setWordWrap(True)
    return label


def scrollable(widget: QWidget) -> QScrollArea:
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setWidget(widget)
    area.setFrameShape(QScrollArea.Shape.NoFrame)
    return area
