# Griffin Persona
<div align="center">
<img width="300" height="300" alt="GriffinPersona" src="https://github.com/user-attachments/assets/998c4d2c-df5e-4aef-8141-9b0cfd5dcc78" />
</div>

**Griffin Persona** is the official welcome screen for Griffin Linux. It helps you get up and running by installing essential drivers and tailoring tools to your specific workflows. 

* **First Boot:** Launches automatically to guide your initial setup.
* **Subsequent Boots:** Behaves as a standard system application whenever you need to adjust your setup.

> **Note:** Griffin Persona sets up your workflow environments but does not install or update core Griffin system tools. For tool updates, please use [Griffin Updater](https://github.com/bobbycomet/GriffinUpdater).

The welcome tool for Griffin Linux, it's what sets up your computer's
*persona*.

## What Griffin Linux is

Griffin Linux is a Linux distribution built for people switching over from
Windows. It's built on top of Kubuntu, but it is an independent project;
it isn't affiliated with, endorsed by, or supported by Canonical, Ubuntu,
or Debian.

A lot of distros aimed at Windows switchers try to hide the terminal away,
as if it's something to be embarrassed about. Griffin Linux doesn't do
that. It **abstracts** the terminal — it gives you a graphical way to do
the things you'd otherwise have to look up and type by hand, but it never
**replaces** the terminal or the package manager underneath it. The
terminal is still right there. `apt` is still `apt`. Nothing about Griffin
Linux locks that away from you or pretends it doesn't exist.

## What does "persona" mean?

Most distros ship as one fixed experience and expect everyone to bend
their setup to fit it. Griffin Linux starts from a different idea: your
computer should be set up around what you actually use it for, not a
generic default that assumes everyone wants the same thing.

That's what a **persona** is, in Griffin Linux terms: the shape your setup
takes based on how you actually use the machine. Someone using their
computer mainly to play Windows games through Proton has a different
persona than someone who mainly streams, or mainly writes code, or just
wants a stable everyday desktop. Neither one is the "correct" way to use
Griffin Linux; they're just different personas, and you're the one who
decides which pieces apply to you.

## Persona is one piece of a larger system

Griffin Persona isn't the whole story; it's the entry point. Griffin
Linux includes several other first-party tools, each handling a distinct
job: **[Grix](https://github.com/bobbycomet/Grix)** is the system troubleshooter, which explains what broke,
offers a fix, and lets you choose whether it handles it or walks you
through doing it yourself. **[FanHub](https://github.com/bobbycomet/Fan-Hub)** controls case/CPU/GPU fans
(including RGB and liquid coolers) with Windows-style fan-curve graphs.
**[Appify](https://github.com/bobbycomet/Appify)** turns websites into isolated, sandboxed desktop apps.
**[Griffin Hub](https://github.com/bobbycomet/Griffin-Hub)**  handles third-partyhardware drivers, and is also home to 
**[Sentry](https://github.com/bobbycomet/Process-Sentry)** (resource throttling and a max-performance mode when you launch a game) 
and **[Kernel Auto-tune](https://github.com/bobbycomet/kernel-autotune-V2)** (kernel-specific tuning, whichever of Xanmod/Liquorix/Mainline you're on).
**[XKM](https://github.com/bobbycomet/XKM-Multi-Kernel-Manager)** manages your installed kernels and DKMS rebuilds. 
**[Griffin Updater](https://github.com/bobbycomet/GriffinUpdater)** keeps Griffin current automatically.
The in-app Welcome page covers all of these in more depth than this README does.

Griffin Persona is the tool that builds that persona. Instead of guessing
what you need or bundling everything together whether you want it or not,
it lays out what's actually available, by workflow, not by jargon, and
you choose. Only setting up Windows games? Just touch the Windows
Compatibility and GPU pages. Building a streaming rig? Add the Gaming and
Audio pages too. Also want a coding environment on the same machine? Add
Development. None of it is mutually exclusive, and none of it is forced —
the computer ends up shaped like whatever you actually told it to be.

## Why this exists

Setting up a Linux machine properly, for gaming, for streaming, for
day-to-day use after switching from Windows, usually means a lot of
guesswork: figuring out which graphics driver packages you actually need,
copying a string of commands from a three-year-old forum post, installing
every Wine helper "just in case" until your setup breaks for reasons you
can't explain, and not finding out your audio or video acceleration is
broken until something actually fails on you.

Griffin Persona exists to replace that guesswork with a few clicks, while
keeping you in control and keeping the terminal in view rather than hidden
behind it. It looks at what's actually on your machine, shows you in plain
language exactly what it's about to change, and only then does it — never
silently, never as a surprise.

## How it actually works

Every section of Griffin Persona follows the same pattern:

1. **It looks at your machine** — what graphics card you have, what's
   already installed, what's currently running.
2. **It shows you sensible choices** — the things most people building
   that kind of persona need are already ticked; more specialized or
   riskier options are there if you want them, left unticked by default.
3. **It tells you exactly what's about to change**, in plain English, with
   the real commands it's about to run shown openly — not a black box.
4. **Only then does it apply it** — and if a change needs admin rights, it
   asks through your system's normal authentication prompt, never a raw
   password typed into a hidden script.

Nothing installs itself silently, and nothing happens without you seeing
it coming first. If you'd rather just read what it would have run and type
it into a terminal yourself, you can; that's the whole point of
abstracting the terminal instead of replacing it.

## What you can build your persona out of

**General** — browsers and everyday apps for anyone who doesn't have a
specific gaming, creative, or development workflow in mind. Every browser
here is a genuinely native package: Falkon comes straight from the
standard repos with no extra source needed, and Firefox is installed
from Mozilla's own official apt repository specifically so you get the
real package instead of Ubuntu quietly handing you a Snap. Flatpak and
Snap support live here too, since the Retro & Emulation section installs
through Flatpak.

**Windows Compatibility** — Wine and Proton set up correctly, plus the
extra pieces (like DXVK) that actually make games run well. The more
fragile, "just in case" add-ons stay off by default, since piling those on
is one of the most common ways a Windows-compatibility setup breaks.

**GPU & Drivers** — figures out whether you have an NVIDIA, AMD, or Intel
graphics card and offers the right driver and graphics setup for it, so
you don't have to know the exact package names yourself. Also detects
whether you're on a laptop or desktop (trusting Kernel Auto-tune's own
read on your machine when it's available, otherwise checking on its own),
and on an NVIDIA laptop with hybrid graphics, offers the PRIME/Optimus
switching tools that setup actually needs. Lets you check that things are
actually working, benchmark, and undo a change if it didn't go the way
you wanted.

**Audio** — sets up your audio stack and gives you a one-click health
check for your microphone, speakers, and Bluetooth.

**Gaming** — performance overlays, RGB lighting control, streaming and
capture tools, a lookup to check whether a specific game's anti-cheat is
known to work on Linux before you buy or install it, and a Retro &
Emulation section (RetroArch, Dolphin, PCSX2, RPCS3, mGBA, melonDS,
Ryujinx via the Ryubing build) installed through Flatpak.

**Creative** — OBS, Kdenlive, Blender, GIMP, Inkscape, Krita, Audacity,
and OpenTabletDriver for drawing tablets (downloaded directly from the
project's GitHub releases, since it isn't in the distro repos) — video,
image, audio, and 3D tools for a content-creation persona.

**Storage & Reliability** — snapshots and backups so a bad update doesn't
cost you anything, plus firmware updates and exporting your applied
profile history.

**Development** — the basics for anyone who also wants to write code on
the same machine: Git, build tools, Python, Node, an editor, Docker.

**Diagnostics** — one checklist that tells you what's working and what
isn't across your whole setup, with a single "fix this" button for
anything that's broken.

## When it runs

Griffin Persona introduces itself once, automatically, the first time you
log in after installing Griffin Linux — that's the "welcome" part. After
that first run, it stops launching on its own and just sits in your
application menu like any other program, ready whenever you want to add
something, check on something, or change your mind about your persona
entirely.

---

## 🚀 Installation

You can install the latest release via the terminal:

```
# Download the package
wget https://github.com/bobbycomet/GriffinPerson/releases/download/v1.0.0/griffin-persona.deb

# Install the package
sudo dpkg -i griffin-persona.deb

# Fix any missing dependencies
sudo apt install -f
```
Or use your package installer or Gdebi

<img width="1920" height="1080" alt="Screenshot_20260707_093617" src="https://github.com/user-attachments/assets/7f5b1a9f-572e-42a0-bc95-6d3ae4b589b6" />
<img width="1920" height="1080" alt="Screenshot_20260707_093627" src="https://github.com/user-attachments/assets/2645a61d-daa8-44d4-95a1-223af4954acb" />
<img width="1920" height="1080" alt="Screenshot_20260707_093635" src="https://github.com/user-attachments/assets/aa482b9d-1103-4c84-acf2-91026387e837" />
<img width="1920" height="1080" alt="Screenshot_20260707_093644" src="https://github.com/user-attachments/assets/a3f64506-21f5-4d6f-872a-48fcb945c00e" />
<img width="1920" height="1080" alt="Screenshot_20260707_093657" src="https://github.com/user-attachments/assets/15d12744-cc36-4f01-b1db-0087476e9266" />
<img width="1920" height="1080" alt="Screenshot_20260707_093707" src="https://github.com/user-attachments/assets/e05a3dc7-2afc-418f-a1f3-1c027fa6977e" />
<img width="1920" height="1080" alt="Screenshot_20260707_093714" src="https://github.com/user-attachments/assets/04b14e42-61d0-4e5a-96a1-169cfe4362a6" />
<img width="1920" height="1080" alt="Screenshot_20260707_093723" src="https://github.com/user-attachments/assets/891cdcdd-5420-4fde-92f2-e8322906615c" />
<img width="1920" height="1080" alt="Screenshot_20260707_093730" src="https://github.com/user-attachments/assets/8118507b-6821-41c8-9b16-1396233e9d7f" />
<img width="1920" height="1080" alt="Screenshot_20260707_093737" src="https://github.com/user-attachments/assets/e3081645-2754-4d13-9a89-9db192a0c621" />

<div align="center">
  <img src="https://raw.githubusercontent.com/bobbycomet/Appify/main/Griffin-G.png" alt="Griffin Linux" width="15%"/>
  <p><strong>Griffin Linux. Where power meets simplicity.</strong><br/>
  Made with Windows switchers in mind. Built for everyone who wants a better PC.</p>
</div>

Griffin Persona is part of the Griffin Linux project. The name Griffin Persona, the Griffin Linux name, and associated icons are protected under the GPLv3 to preserve the integrity of the branding in all distributed versions.
