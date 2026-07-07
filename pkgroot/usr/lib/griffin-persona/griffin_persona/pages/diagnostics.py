"""Diagnostics page — turns 'install these 9 packages' into 'click repair'."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from .. import diagnostics, state
from ..packages import Component
from ..widgets import confirm_and_apply, section_subtitle, section_title


class DiagnosticsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.addWidget(section_title("System Diagnostics"))
        outer.addWidget(section_subtitle(
            "One checklist, one Repair button. Anything not OK gets a ready-made fix."
        ))

        top_row = QHBoxLayout()
        self.rerun_btn = QPushButton("Run Diagnostics")
        self.rerun_btn.setObjectName("Primary")
        self.rerun_btn.clicked.connect(self.run_checks)
        top_row.addWidget(self.rerun_btn)
        self.repair_all_btn = QPushButton("Repair All")
        self.repair_all_btn.clicked.connect(self._repair_all)
        top_row.addWidget(self.repair_all_btn)
        top_row.addStretch()
        outer.addLayout(top_row)

        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.results_container)
        outer.addWidget(scroll)

        self._last_results = []
        self.run_checks()

    def run_checks(self):
        for i in reversed(range(self.results_layout.count())):
            item = self.results_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()

        results = diagnostics.run_all()
        self._last_results = results
        for r in results:
            row = QWidget()
            h = QHBoxLayout(row)
            symbol, obj = {"ok": ("✓", "StatusOk"), "warn": ("⚠", "StatusWarn"), "bad": ("⚠", "StatusBad")}[r.status]
            status_label = QLabel(f"{symbol} {r.label}")
            status_label.setObjectName(obj)
            h.addWidget(status_label)
            if r.detail:
                detail = QLabel(r.detail)
                detail.setObjectName("Muted")
                h.addWidget(detail)
            h.addStretch()
            if r.status != "ok" and (r.fix_packages or r.fix_user_action):
                fix_btn = QPushButton("Repair")
                fix_btn.clicked.connect(lambda _, res=r: self._repair_one(res))
                h.addWidget(fix_btn)
            self.results_layout.addWidget(row)

        try:
            state.SYSTEM_STATE_DIR  # noqa: B018 - just reference, write happens via helper normally
        except Exception:
            pass
        self._save_snapshot(results)

    def _save_snapshot(self, results):
        # Best-effort, local copy for the person's own reference; the canonical
        # system snapshot under /var/lib/griffin-postinstall is written by the
        # privileged helper after a Repair All run, not by the GUI directly.
        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results": [{"id": r.id, "label": r.label, "status": r.status, "detail": r.detail} for r in results],
        }
        try:
            from pathlib import Path
            local = Path.home() / ".config" / "griffin-persona" / "last-diagnostics.json"
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text(json.dumps(snapshot, indent=2))
        except OSError:
            pass

    def _repair_one(self, result):
        components = []
        if result.fix_packages:
            components.append(Component(f"fix_{result.id}", result.label, result.detail, packages=result.fix_packages))
        if result.fix_user_action:
            components.append(Component(f"fix_{result.id}_ua", result.label, result.detail, user_action=result.fix_user_action))
        from .. import actions
        plan = actions.build_plan(components)
        confirm_and_apply(self, plan)
        self.run_checks()

    def _repair_all(self):
        from .. import actions
        components = []
        for r in diagnostics.repairable(self._last_results):
            if r.fix_packages:
                components.append(Component(f"fix_{r.id}", r.label, r.detail, packages=r.fix_packages))
            if r.fix_user_action:
                components.append(Component(f"fix_{r.id}_ua", r.label, r.detail, user_action=r.fix_user_action))
        plan = actions.build_plan(components)
        confirm_and_apply(self, plan)
        self.run_checks()
