"""Welcome page — shown first on initial boot, reachable anytime afterwards."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget,
)

from .. import state

ASSETS = Path(__file__).resolve().parent.parent / "assets"


class WelcomePage(QWidget):
    def __init__(self, on_get_started, parent=None):
        super().__init__(parent)
        self._on_get_started = on_get_started

        outer = QVBoxLayout(self)
        outer.setContentsMargins(48, 36, 48, 36)
        outer.setSpacing(18)

        header = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(QPixmap(str(ASSETS / "griffin_persona.png")).scaledToHeight(
            120, Qt.TransformationMode.SmoothTransformation))
        header.addWidget(logo)

        grix = QLabel()
        grix.setPixmap(QPixmap(str(ASSETS / "grix.png")).scaledToHeight(
            150, Qt.TransformationMode.SmoothTransformation))
        header.addStretch()
        header.addWidget(grix)
        outer.addLayout(header)

        title = QLabel("Welcome to Griffin")
        title.setObjectName("PageTitle")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        outer.addWidget(title)

        subtitle = QLabel(
            "Griffin is a tailored Linux KDE experience built on top of Kubuntu — no "
            "affiliation with Ubuntu, Canonical, Kubuntu, or Debian. This page is a quick "
            "tour of the whole system, not just the tool you're looking at right now."
        )
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)
        outer.addWidget(subtitle)

        outer.addWidget(self._explainer(
            "What Griffin actually is",
            "Most distros that try to make switching from Windows easy do it mostly with "
            "looks — a familiar layout, a familiar theme — while the system underneath "
            "stays exactly as hidden as everywhere else. Griffin's approach is different: "
            "Griffin won't hide the kernel, Griffin abstracts it. The terminal, the package "
            "manager, the kernel — none of it is locked away or pretended out of existence. "
            "Griffin just gives you a graphical way in, built specifically with Windows "
            "users in mind, to make that transition easier without treating you like you "
            "can't eventually learn what's underneath."
        ))

        outer.addWidget(self._explainer(
            "Persona — you're using it right now",
            "Griffin starts with Persona: the tool for defining your own workflows instead "
            "of accepting a one-size-fits-all setup. Every page in this app — General, "
            "Windows Compatibility, GPU & Drivers, Audio, Gaming, Creative, Storage, "
            "Development — is a piece of persona you opt into. Nobody else's idea of what "
            "your computer is for gets forced onto you."
        ))

        outer.addWidget(self._explainer(
            "Grix — the troubleshooter",
            "Grix is Griffin's troubleshooter. When something breaks, Grix explains why in "
            "plain language, offers a fix, and then gives you the choice: let Grix handle "
            "it, or walk through doing it yourself. Either way, Grix teaches the underlying "
            "Linux concept and how to troubleshoot it, so you're never just clicking a "
            "button blindly — and never stuck figuring it out alone."
        ))

        outer.addWidget(self._explainer(
            "FanHub",
            "FanHub controls your case fans, CPU fan, and GPU fan, including RGB and liquid "
            "coolers — with fan-curve graphs that look and feel like what you'd expect from "
            "Windows fan-control software, not a buried config file."
        ))

        outer.addWidget(self._explainer(
            "Appify",
            "Appify turns websites into real desktop apps. Unlike most PWA tools, Appify is "
            "built around isolation — no shared browser profiles, real extension support, "
            "and since each one is treated as its own app rather than a browser tab, "
            "telemetry back to your main browser is limited. Appify is also cloud-gaming "
            "ready, as part of making your desktop work the way you actually want it to."
        ))

        outer.addWidget(self._explainer(
            "WinBridge",
            "Persona installs Wine and Proton in general. WinBridge is where you set up "
            "the environment for a specific app — its own Wine prefix, its own settings, "
            "tuned per-app instead of system-wide. WinBridge is also where you reach for "
            "hardware: installing third-party drivers when you genuinely need them — "
            "extended driver support for Xbox controllers, sim racing wheels, Wi-Fi cards, "
            "and more. WinBridge is also home to Sentry and Kernel Auto-tune."
        ))

        outer.addWidget(self._explainer(
            "Sentry",
            "Sentry controls how the system shares its resources. If a browser tab starts "
            "eating CPU, Sentry reins it in so your processor isn't screaming under a load "
            "that has nothing to do with what you're actually trying to do. The moment you "
            "launch a game, Sentry shifts the system into a maximum-performance power "
            "state, so the game gets everything available — minus what the system itself "
            "genuinely needs to keep running."
        ))

        outer.addWidget(self._explainer(
            "Kernel Auto-tune",
            "Kernel Auto-tune does something different from Sentry, even though the two "
            "work together to make the system predictable: it sets the kernel's own "
            "parameters. It doesn't matter which kernel you're running — Xanmod, Liquorix, "
            "or Mainline — Kernel Auto-tune looks at your hardware and your kernel together "
            "and configures the best environment for that specific combination."
        ))

        outer.addWidget(self._explainer(
            "XKM",
            "XKM handles your kernels. If you're coming from Windows, you've probably never "
            "had to think about DKMS — but it matters, since it's what keeps drivers built "
            "against whatever kernel you're running. XKM lets you install kernels, remove "
            "old ones, lock a kernel in place, rebuild every DKMS module for it (where the "
            "kernel supports that), and more. PPAs are also managed through XKM."
        ))

        outer.addWidget(self._explainer(
            "Discord Updater",
            "Discord has no built-in way to update itself on Linux beyond manually "
            "downloading a new file and reinstalling it by hand. Discord Updater automates "
            "the whole thing: it checks the current version, and — at 3 AM, if the machine "
            "is on — shuts Discord down, updates it, removes the old file, and has it ready "
            "to go the next time you open it."
        ))

        outer.addWidget(self._explainer(
            "Why all of this exists",
            "Every one of these tools is pointed at the same goal: making Griffin work as "
            "close to a Windows workflow as possible — including gaming, which is also why "
            "Griffin ships with EmulationStation preinstalled."
        ))

        outer.addWidget(self._explainer(
            "What you'll find in Persona specifically",
            "• General — browsers and everyday apps for a good default desktop\n"
            "• Windows Compatibility — Wine, Proton, DXVK and the launchers that use them\n"
            "• GPU & Drivers — vendor-specific profiles you preview before applying\n"
            "• Audio — a PipeWire stack with a one-page health check\n"
            "• Gaming — overlays, RGB control, streaming, capture, and retro/emulation\n"
            "• Creative — video, image, audio and 3D tools for content creation\n"
            "• Storage & Reliability — snapshots, firmware updates, backup export\n"
            "• Development — the basics for building things on Griffin Linux\n"
            "• Diagnostics — a single checklist and a single Repair button"
        ))

        outer.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        footer = QHBoxLayout()
        footer.addStretch()
        cta = QPushButton("Get Started")
        cta.setObjectName("Primary")
        cta.setMinimumWidth(160)
        cta.clicked.connect(self._handle_get_started)
        footer.addWidget(cta)
        outer.addLayout(footer)

    def _explainer(self, heading: str, body: str) -> QWidget:
        box = QWidget()
        box.setObjectName("Card")
        layout = QVBoxLayout(box)
        h = QLabel(heading)
        h.setObjectName("SectionHeader")
        layout.addWidget(h)
        b = QLabel(body)
        b.setWordWrap(True)
        layout.addWidget(b)
        return box

    def _handle_get_started(self):
        state.mark_welcome_seen()
        if self._on_get_started:
            self._on_get_started()
