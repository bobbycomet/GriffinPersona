"""Griffin Persona — main window."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QListWidget, QListWidgetItem, QMainWindow, QSplitter, QStackedWidget

from . import state
from .pages.audio import AudioPage
from .pages.creative import CreativePage
from .pages.development import DevelopmentPage
from .pages.diagnostics import DiagnosticsPage
from .pages.gaming import GamingPage
from .pages.general import GeneralPage
from .pages.gpu_drivers import GpuDriversPage
from .pages.storage import StoragePage
from .pages.welcome import WelcomePage
from .pages.windows_compat import WindowsCompatPage
from .theme import STYLESHEET
from .widgets import scrollable

ASSETS = Path(__file__).resolve().parent / "assets"

NAV_ITEMS = [
    "Welcome",
    "General",
    "Windows Compatibility",
    "GPU & Drivers",
    "Audio",
    "Gaming",
    "Creative",
    "Storage & Reliability",
    "Development",
    "Diagnostics",
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Griffin Persona")
        self.setWindowIcon(QIcon(str(ASSETS / "griffin_persona.png")))
        self.resize(1080, 720)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        for name in NAV_ITEMS:
            QListWidgetItem(name, self.sidebar)

        self.stack = QStackedWidget()
        self.stack.addWidget(scrollable(WelcomePage(on_get_started=self._go_to_windows_compat)))
        self.stack.addWidget(scrollable(GeneralPage()))
        self.stack.addWidget(scrollable(WindowsCompatPage()))
        self.stack.addWidget(scrollable(GpuDriversPage()))
        self.stack.addWidget(scrollable(AudioPage()))
        self.stack.addWidget(scrollable(GamingPage()))
        self.stack.addWidget(scrollable(CreativePage()))
        self.stack.addWidget(scrollable(StoragePage()))
        self.stack.addWidget(scrollable(DevelopmentPage()))
        self.stack.addWidget(DiagnosticsPage())

        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.stack)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        self.statusBar().showMessage("Ready")

    def _go_to_windows_compat(self):
        self.sidebar.setCurrentRow(NAV_ITEMS.index("Windows Compatibility"))


def main() -> int:
    autostart_mode = "--autostart" in sys.argv

    app = QApplication(sys.argv)
    app.setApplicationName("Griffin Persona")
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    if autostart_mode and state.has_seen_welcome():
        # Safety net: if the per-user autostart override somehow didn't take
        # (e.g. a fresh ~/.config), don't loop the welcome flow forever.
        window.sidebar.setCurrentRow(NAV_ITEMS.index("Diagnostics"))
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
