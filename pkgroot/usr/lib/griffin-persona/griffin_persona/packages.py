"""
Griffin Persona — component catalog.

This module is pure data. Every installable thing in the app is a
``Component``: a name, a description, and either a list of apt package
names (applied through the privileged helper) or a ``user_action`` key
naming a small unprivileged routine (e.g. downloading Proton-GE into the
user's own Steam directory — that needs no root at all).

Nothing here executes anything. Pages render this catalog as checkboxes,
build a preview ("here is exactly what will change"), and only then call
into privileged.py or the relevant user_action handler.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Component:
    id: str
    name: str
    description: str
    packages: list[str] = field(default_factory=list)
    user_action: str | None = None
    recommended: bool = False
    requires_i386: bool = False


# ---------------------------------------------------------------------------
# GPU / Driver layer — profiles are *previewed* before anything is applied.
# ---------------------------------------------------------------------------

GPU_PROFILES: dict[str, list[Component]] = {
    "nvidia": [
        Component("nv_driver", "Proprietary driver",
                   "Auto-detected via Ubuntu's own driver tool at apply time — never a hardcoded "
                   "version, so this can't go stale or pick the wrong build for your card.",
                   user_action="install_nvidia_driver_auto", recommended=True),
        Component("nv_vulkan", "Vulkan (64-bit)", "Vulkan loader and ICD for the proprietary driver.",
                   packages=["libvulkan1", "vulkan-tools"], recommended=True),
        Component("nv_vulkan32", "Vulkan (32-bit)", "Needed for most Wine/Proton titles and older 32-bit games.",
                   packages=["libvulkan1:i386"], requires_i386=True, recommended=True),
        Component("nv_nvenc", "NVENC support", "Hardware video encode, used by OBS, Sunshine and GPU screen recorders.",
                   packages=["libnvidia-encode1"], recommended=True),
        Component("nv_cuda", "CUDA toolkit", "Only needed for compute/ML workloads, not gaming.",
                   packages=["nvidia-cuda-toolkit"]),
        Component("nv_mangohud", "MangoHud", "On-screen FPS/frametime/thermal overlay.",
                   packages=["mangohud"], recommended=True),
        Component("nv_gamescope", "Gamescope tuning", "Micro-compositor for scaling, frame limiting and HDR-ish tricks.",
                   packages=["gamescope"]),
        Component("nv_vaapi", "VA-API video decode (Firefox/Chrome)",
                   "NVIDIA's driver has no native VA-API support, so this installs the "
                   "community nvidia-vaapi-driver bridge and sets the environment variables "
                   "apps need to find it. Decode only — there's no encode side, that's what "
                   "NVENC above is for. Reliable in Firefox/Chrome; VLC and mpv are known to "
                   "behave inconsistently with it. On some setups this can use more power than "
                   "plain CPU decode (an NVIDIA driver limitation, not a bug here) — on driver "
                   "580.105.08+ a documented workaround is applied automatically.",
                   user_action="configure_nvidia_vaapi"),
    ],    "amd": [
        Component("amd_mesa", "Mesa (RadeonSI/RADV)", "Open-source userspace driver stack for AMD GPUs.",
                   packages=["mesa-vulkan-drivers", "libgl1-mesa-dri"], recommended=True),
        Component("amd_vulkan32", "Vulkan (32-bit / RADV)", "32-bit Vulkan ICD, needed for Wine/Proton titles.",
                   packages=["mesa-vulkan-drivers:i386"], requires_i386=True, recommended=True),
        Component("amd_firmware", "GPU firmware", "Up-to-date firmware blobs for newer RDNA hardware.",
                   packages=["firmware-amd-graphics"], recommended=True),
        Component("amd_rocm", "ROCm (compute)", "Only needed for compute/ML workloads, not gaming.",
                   packages=["rocm-smi"]),
        Component("amd_mangohud", "MangoHud", "On-screen FPS/frametime/thermal overlay.",
                   packages=["mangohud"], recommended=True),
        Component("amd_gamescope", "Gamescope tuning", "Micro-compositor for scaling and frame limiting.",
                   packages=["gamescope"]),
    ],
    "intel": [
        Component("intel_mesa", "Mesa (Iris/ANV)", "Open-source userspace driver stack for Intel GPUs.",
                   packages=["mesa-vulkan-drivers", "libgl1-mesa-dri"], recommended=True),
        Component("intel_media", "Media / VAAPI stack", "Hardware video decode/encode for browsers and players.",
                   packages=["intel-media-va-driver-non-free", "vainfo"], recommended=True),
        Component("intel_vulkan32", "Vulkan (32-bit / ANV)", "32-bit Vulkan ICD, needed for Wine/Proton titles.",
                   packages=["mesa-vulkan-drivers:i386"], requires_i386=True, recommended=True),
        Component("intel_mangohud", "MangoHud", "On-screen FPS/frametime/thermal overlay.",
                   packages=["mangohud"]),
    ],
}

GPU_ACTIONS = ["Validate Driver", "Validate Vulkan", "Benchmark", "Repair", "Rollback"]

# ---------------------------------------------------------------------------
# Laptop / hybrid graphics (NVIDIA Optimus and similar) — shown on the GPU &
# Drivers page specifically when more than one GPU vendor is detected
# (typically Intel or AMD integrated + NVIDIA discrete). The proprietary
# driver above already covers the discrete GPU itself; these are the extra
# pieces an Optimus-style laptop specifically needs: a way to switch which
# GPU renders what, and a way to actually see what's happening on the
# discrete GPU day to day.
#
# EnvyControl was deliberately left out: its GitHub repo was archived by the
# maintainer (no longer developed) and the latest release has no .deb asset
# attached despite the README's own install instructions claiming there is
# one — wiring it in would mean a button that just doesn't work, the same
# call already made for Citron and Eden in Retro & Emulation.
# ---------------------------------------------------------------------------

NVIDIA_LAPTOP_COMPONENTS: list[Component] = [
    Component("nv_prime", "NVIDIA PRIME (nvidia-prime)", "Ubuntu's own tool for switching between "
               "graphics modes on Optimus laptops — gives you prime-select on-demand (power-saving, "
               "GPU used only when an app asks for it) and prime-select nvidia (NVIDIA full-time). "
               "This is the standard, lowest-risk option and the one to reach for first.",
               packages=["nvidia-prime"], recommended=True),
    Component("nv_settings", "NVIDIA X Server Settings", "GUI for checking your driver version, "
               "thermal metrics, and which applications are currently using the discrete GPU.",
               packages=["nvidia-settings"], recommended=True),
    Component("nv_switcheroo", "Switcheroo Control", "An actively-maintained, desktop-integrated "
               "alternative to PRIME for per-app GPU selection — also works on AMD/Intel hybrid "
               "setups, not just NVIDIA. Don't run this alongside actively switching PRIME profiles "
               "at the same time; pick one approach.",
               packages=["switcheroo-control"]),
]

VKMARK_COMPONENT = Component("vkmark", "vkmark", "Lightweight Vulkan benchmark used by the Benchmark button.",
                              packages=["vkmark"])


# ---------------------------------------------------------------------------
# Windows Compatibility
# ---------------------------------------------------------------------------

WIN_CORE: list[Component] = [
    Component("win_i386", "i386 architecture", "Enables 32-bit packages; almost everything below needs this.",
               user_action="enable_i386", recommended=True),
    Component("win_wine", "Wine", "The core Windows compatibility layer.",
               packages=["wine"], recommended=True),
    Component("win_winetricks", "Winetricks", "Helper for installing Windows runtime components into prefixes.",
               packages=["winetricks"], recommended=True),
    Component("win_common_deps", "Common dependencies", "cabextract, p7zip, unzip and fonts most installers expect.",
               packages=["cabextract", "p7zip-full", "unzip", "fontconfig"], recommended=True),
]

WIN_RUNNERS: list[Component] = [
    Component("run_wine_stable", "Wine Stable", "Official upstream stable branch via WineHQ.",
               user_action="install_winehq_stable", recommended=True),
    Component("run_wine_staging", "Wine Staging", "Bleeding-edge patches not yet in stable; better game compat, less stable.",
               user_action="install_winehq_staging"),
    Component("run_wine_ge", "Wine-GE", "GloriousEggroll's Wine build, tuned for Lutris game compatibility.",
               user_action="install_wine_ge"),
    Component("run_proton_ge", "Proton-GE", "Community Proton build with extra patches, installs into Steam's compat tools.",
               user_action="install_proton_ge", recommended=True),
    Component("run_proton_experimental", "Proton Experimental", "Managed by Steam itself — this just verifies it's present.",
               user_action="verify_proton_experimental"),
]

WIN_RUNTIME_RECOMMENDED: list[Component] = [
    Component("rt_corefonts", "Corefonts", "Core Windows fonts most installers expect to find.",
               user_action="winetricks:corefonts", recommended=True),
    Component("rt_vcrun2022", "VC++ 2022 runtime", "Visual C++ redistributable, the most commonly required one.",
               user_action="winetricks:vcrun2022", recommended=True),
    Component("rt_dxvk", "DXVK", "Translates Direct3D 9/10/11 to Vulkan — the single biggest perf win for most games.",
               user_action="install_dxvk", recommended=True),
]

WIN_RUNTIME_OPTIONAL: list[Component] = [
    Component("rt_vkd3d", "VKD3D-Proton", "Translates Direct3D 12 to Vulkan, for DX12 titles."),
    Component("rt_dotnet48", "dotnet48", "Older .NET runtime some installers still need.", user_action="winetricks:dotnet48"),
    Component("rt_d3dx9", "d3dx9", "Legacy DirectX 9 component libraries.", user_action="winetricks:d3dx9"),
    Component("rt_xact", "xact", "DirectX audio engine used by some older titles.", user_action="winetricks:xact"),
    Component("rt_mf", "Media Foundation (mf)", "Needed by some game cutscenes/launchers.", user_action="winetricks:mf"),
]

WIN_LAUNCHERS: list[Component] = [
    Component("lnc_lutris", "Lutris", "Open-source game manager that wraps Wine/Proton runners.",
               packages=["lutris"], recommended=True),
    Component("lnc_bottles", "Bottles", "Sandboxed, per-app Wine prefix manager (Flatpak).",
               user_action="flatpak:com.usebottles.bottles"),
    Component("lnc_steam", "Steam", "Valve's launcher and the source of Proton.",
               packages=["steam-installer"], recommended=True),
    Component("lnc_heroic", "Heroic Games Launcher", "Open-source Epic/GOG/Amazon launcher (Flatpak).",
               user_action="flatpak:com.heroicgameslauncher.hgl"),
]

WIN_REPAIR_ACTIONS = ["Reset prefix", "Rebuild symlinks", "Verify Vulkan", "Dependency diagnostics"]


# ---------------------------------------------------------------------------
# Audio layer (PipeWire-centric)
# ---------------------------------------------------------------------------

AUDIO_COMPONENTS: list[Component] = [
    Component("au_pipewire", "PipeWire", "Modern audio/video server replacing PulseAudio.",
               packages=["pipewire", "pipewire-pulse"], recommended=True),
    Component("au_wireplumber", "WirePlumber", "Session manager for PipeWire (routing policy).",
               packages=["wireplumber"], recommended=True),
    Component("au_jack", "PipeWire-JACK", "JACK compatibility for pro-audio apps.", packages=["pipewire-jack"]),
    Component("au_bt_codecs", "Bluetooth codecs", "aptX/LDAC/AAC support for Bluetooth audio.",
               packages=["libspa-0.2-bluetooth"], recommended=True),
    Component("au_easyeffects", "EasyEffects", "System-wide equalizer/effects (noise suppression, limiter, etc).",
               packages=["easyeffects"]),
    Component("au_latency_preset", "Gaming latency preset", "Lowers PipeWire's quantum for reduced audio latency.",
               user_action="apply_audio_latency_preset"),
    Component("au_pavucontrol", "PAVUcontrol", "Per-app volume mixer and device routing — works fine against "
               "PipeWire's PulseAudio-compatibility layer.",
               packages=["pavucontrol"], recommended=True),
    Component("au_soundconverter", "SoundConverter", "Batch-converts audio files between formats.",
               packages=["soundconverter"]),
]

AUDIO_HEALTH_CHECKS = ["Mic", "Output", "JACK", "Bluetooth", "Sample Rate"]


# ---------------------------------------------------------------------------
# Gaming layer
# ---------------------------------------------------------------------------

GAMING_COMPONENTS: list[Component] = [
    Component("gm_gamemode", "GameMode", "Requests CPU governor / scheduling tweaks while games run.",
               packages=["gamemode"], recommended=True),
    Component("gm_mangohud", "MangoHud", "On-screen performance overlay.", packages=["mangohud"], recommended=True),
    Component("gm_goverlay", "GOverlay", "GUI for configuring MangoHud and vkBasalt presets without hand-editing config files.",
               packages=["goverlay"]),
    Component("gm_protontricks", "Protontricks", "Runs winetricks against a specific Steam/Proton game's "
               "prefix — for fixing an individual game rather than your whole Wine setup.",
               packages=["protontricks"]),
    Component("gm_corectrl", "CoreCtrl", "GPU/CPU clocks, fan curves and power profiles (AMD-focused).",
               packages=["corectrl"]),
    Component("gm_openrgb", "OpenRGB", "Vendor-neutral RGB lighting control.", packages=["openrgb"]),
    Component("gm_lact", "LACT", "AMD GPU overclock/fan-curve control daemon + GUI.", user_action="install_lact"),
    Component("gm_controllers", "Controller support bundle", "udev rules + Steam Input deps for common pads.",
               packages=["steam-devices"], recommended=True),
    Component("gm_gamescope", "Gamescope", "Micro-compositor for scaling/FSR/frame limiting.", packages=["gamescope"]),
    Component("gm_sunshine", "Sunshine", "Self-hosted game-stream host (Moonlight server).", user_action="install_sunshine"),
    Component("gm_moonlight", "Moonlight", "Game-stream client for Sunshine/GeForce NOW hosts.", packages=["moonlight-qt"]),
]

ANTI_CHEAT_NOTE = (
    "Superseded by the functional checker on the Gaming page (backed by the "
    "AreWeAntiCheatYet community dataset) — kept here only for backwards compatibility."
)


# ---------------------------------------------------------------------------
# Retro & Emulation — all via Flatpak, per-system. Every ID below was checked
# against Flathub directly rather than assumed. Two well-known names are
# deliberately NOT here: Citron has only an open, unfulfilled package
# request on Flathub (no actual build exists), and Eden has no verified
# Flathub listing either — shipping either would mean a button that doesn't
# actually work. Waydroid is also left out: it needs kernel-level binder/
# ashmem support that isn't guaranteed across every kernel Griffin Linux
# offers (Xanmod/Liquorix/Mainline), and that's a job for Kernel Auto-tune
# to get right, not a Flatpak checkbox.
# ---------------------------------------------------------------------------

RETRO_EMULATION_COMPONENTS: list[Component] = [
    Component("re_retroarch", "RetroArch", "Frontend for dozens of console/handheld cores in one app — "
               "the place to start if you're not sure which single-system emulator you want yet.",
               user_action="flatpak:org.libretro.RetroArch", recommended=True),
    Component("re_dolphin", "Dolphin", "GameCube and Wii — excellent compatibility and performance.",
               user_action="flatpak:org.DolphinEmu.dolphin-emu"),
    Component("re_pcsx2", "PCSX2", "PlayStation 2 — mature and highly compatible. You'll need your own "
               "legally-dumped PS2 BIOS file.",
               user_action="flatpak:net.pcsx2.PCSX2"),
    Component("re_rpcs3", "RPCS3", "PlayStation 3 — very good but demanding; wants a strong CPU/GPU and "
               "your own legally-dumped PS3 firmware. This Flatpak is community-packaged, not built by "
               "the RPCS3 team directly.",
               user_action="flatpak:net.rpcs3.RPCS3"),
    Component("re_mgba", "mGBA", "Game Boy / Game Boy Advance — accurate and fast.",
               user_action="flatpak:io.mgba.mGBA"),
    Component("re_melonds", "melonDS", "Nintendo DS and DSi.",
               user_action="flatpak:net.kuribo64.melonDS"),
    Component("re_ryujinx", "Ryujinx (Ryubing build)", "Nintendo Switch, via the actively-maintained "
               "Ryubing continuation of Ryujinx. You'll need your own keys and firmware dumped from "
               "your own console.",
               user_action="flatpak:io.github.ryubing.Ryujinx"),
]


# ---------------------------------------------------------------------------
# Storage / reliability layer
# ---------------------------------------------------------------------------

STORAGE_COMPONENTS: list[Component] = [
    Component("st_timeshift", "Timeshift", "Scheduled system snapshots and one-click restore.",
               packages=["timeshift"], recommended=True),
    Component("st_btrfs_assistant", "BTRFS Assistant", "Snapshot/subvolume management GUI (only relevant on btrfs root).",
               packages=["btrfs-assistant"]),
    Component("st_btrfs_progs", "btrfs-progs", "The underlying btrfs command-line tools BTRFS Assistant wraps — "
               "useful on its own if you'd rather work from a terminal.",
               packages=["btrfs-progs"]),
    Component("st_fwupd", "Firmware updater", "fwupd + GUI front-end for UEFI/peripheral firmware updates.",
               packages=["fwupd", "gnome-firmware"]),
    Component("st_gparted", "GParted", "Partition editor — resize, create, delete, move partitions.",
               packages=["gparted"]),
    Component("st_preload", "Preload", "Adaptive readahead daemon that learns which apps you open most "
               "and helps them start faster over time.",
               packages=["preload"]),
    Component("st_zram", "zram-tools", "Compressed RAM-backed swap — helps on systems with less memory "
               "without wearing down an SSD the way disk swap does.",
               packages=["zram-tools"], recommended=True),
    Component("st_earlyoom", "earlyoom", "Steps in before the kernel's own out-of-memory killer, picking "
               "the worst offender sooner so the rest of the system stays responsive.",
               packages=["earlyoom"], recommended=True),
    Component("st_stacer", "Stacer", "System monitor, startup-app manager and cleaner in one GUI.",
               packages=["stacer"]),
    Component("st_bleachbit", "BleachBit", "Disk space and privacy cleaner — caches, logs, temp files.",
               packages=["bleachbit"]),
    Component("st_tlp", "TLP", "Laptop power management for meaningfully better battery life. Skip "
               "this one on a desktop.",
               packages=["tlp", "tlp-rdw"]),
    Component("st_backup_export", "Backup profile export", "Exports your applied Griffin Persona profile history to a file.",
               user_action="export_profile_backup"),
]


# ---------------------------------------------------------------------------
# Development layer
# ---------------------------------------------------------------------------

DEV_COMPONENTS: list[Component] = [
    Component("dev_git", "Git", "Version control.", packages=["git"], recommended=True),
    Component("dev_build_essential", "Build Essentials", "gcc/g++/make and friends for building from source.",
               packages=["build-essential"], recommended=True),
    Component("dev_python", "Python 3 + pip", "Interpreter, venv and pip.", packages=["python3", "python3-pip", "python3-venv"]),
    Component("dev_node", "Node.js + npm", "JavaScript runtime via the distro repos.", packages=["nodejs", "npm"]),
    Component("dev_vscode", "VS Code", "Microsoft's editor (.deb from the official repo).", user_action="install_vscode_repo"),
    Component("dev_vscodium", "VSCodium", "Telemetry-free VS Code build, as an alternative to the above.",
               user_action="flatpak:com.vscodium.codium"),
    Component("dev_docker", "Docker Engine", "Containers, via Docker's official apt repo.", user_action="install_docker_repo"),
    Component("dev_curl_wget", "curl + wget", "The two command-line tools almost everything else assumes you already have.",
               packages=["curl", "wget"], recommended=True),
    Component("dev_aria2", "aria2", "Multi-connection download accelerator/manager for the command line.",
               packages=["aria2"]),
    Component("dev_net_tools", "net-tools", "Legacy networking commands (ifconfig, netstat) some older "
               "scripts and habits still expect, alongside the modern iproute2 tools already on the system.",
               packages=["net-tools"]),
    Component("dev_ssh_server", "OpenSSH Server", "Lets you connect to this machine remotely over SSH — "
               "opens a network service, so left off by default. Only turn this on if you actually want "
               "remote access to this machine.",
               packages=["openssh-server"]),
    Component("dev_wireguard", "WireGuard", "Modern, fast VPN protocol and tools.",
               packages=["wireguard"]),
    Component("dev_openvpn", "OpenVPN", "OpenVPN client plus the NetworkManager integration to manage "
               "connections from the system tray instead of the command line.",
               packages=["openvpn", "network-manager-openvpn"]),
]


# ---------------------------------------------------------------------------
# Creative persona
# ---------------------------------------------------------------------------

CREATIVE_COMPONENTS: list[Component] = [
    Component("cr_obs", "OBS Studio", "Recording and streaming — the same package as on the Gaming page, "
               "listed here too since it's just as central to a creative workflow.",
               packages=["obs-studio"], recommended=True),
    Component("cr_kdenlive", "Kdenlive", "KDE's full video editor — multitrack timeline, effects, color grading.",
               packages=["kdenlive"], recommended=True),
    Component("cr_blender", "Blender", "3D modeling, animation, sculpting, video editing and compositing.",
               packages=["blender"], recommended=True),
    Component("cr_gimp", "GIMP", "Raster image editing — the closest thing to a Linux-native Photoshop.",
               packages=["gimp"], recommended=True),
    Component("cr_inkscape", "Inkscape", "Vector graphics — logos, illustrations, scalable artwork.",
               packages=["inkscape"]),
    Component("cr_krita", "Krita", "Digital painting, sketching and illustration, with strong tablet support.",
               packages=["krita"]),
    Component("cr_audacity", "Audacity", "Multitrack audio recording and editing.",
               packages=["audacity"]),
    Component("cr_opentabletdriver", "OpenTabletDriver", "Driver and configuration UI for drawing tablets "
               "(Wacom, Huion, XP-Pen and others) — only relevant if you actually have one. Downloads the "
               "latest release directly from the project's GitHub, since the package isn't in the distro repos.",
               user_action="install_opentabletdriver"),
    Component("cr_shotcut", "Shotcut", "Another full video editor, as an alternative to Kdenlive.",
               packages=["shotcut"]),
    Component("cr_pitivi", "Pitivi", "A simpler, more lightweight video editor than Kdenlive or Shotcut.",
               packages=["pitivi"]),
    Component("cr_godot3", "Godot 3", "2D/3D game engine, the 3.x line — still the right choice for some "
               "older projects and a simpler GDScript-only workflow.",
               packages=["godot3"]),
    Component("cr_godot4", "Godot 4", "The current Godot line. No apt package exists for it, so this "
               "installs the community-maintained Flatpak build — it's reliable for most people, but if "
               "you hit editor issues, the official .zip from godotengine.org is the fallback the Godot "
               "community itself usually points to.",
               user_action="flatpak:org.godotengine.Godot"),
    Component("cr_ffmpeg", "FFmpeg", "The command-line video/audio toolkit nearly everything else "
               "(including several apps on this page) builds on.",
               packages=["ffmpeg"], recommended=True),
    Component("cr_handbrake", "HandBrake", "GUI video transcoder — shrink files, change formats, prep "
               "video for a specific device.",
               packages=["handbrake"]),
    Component("cr_yt_dlp", "yt-dlp", "Command-line downloader for YouTube and a long list of other "
               "video/audio sites.",
               packages=["yt-dlp"]),
    Component("cr_imagemagick", "ImageMagick", "Command-line image conversion and batch editing.",
               packages=["imagemagick"]),
    Component("cr_mpv", "mpv", "Lightweight, scriptable media player — many people's preferred player "
               "over VLC once they've tried it.",
               packages=["mpv"]),
    Component("cr_celluloid", "Celluloid", "A proper GTK front-end for mpv, for anyone who wants mpv's "
               "playback quality without living in a config file.",
               packages=["celluloid"]),
]


# ---------------------------------------------------------------------------
# General persona — browsers and everyday apps for people who just want a
# good default desktop, not a specific gaming/creative/dev workflow.
# ---------------------------------------------------------------------------

GENERAL_COMPONENTS: list[Component] = [
    Component("gn_falkon", "Falkon", "KDE's own native browser — comes straight from the standard repos, "
               "no extra software source needed at all.",
               packages=["falkon"], recommended=True),
    Component("gn_firefox", "Firefox", "Installed from Mozilla's own official apt repository rather than "
               "Ubuntu's, which would otherwise quietly hand you a Snap-wrapped version instead of a "
               "native package.",
               user_action="install_firefox_repo", recommended=True),
    Component("gn_brave", "Brave", "Chromium-based, with built-in ad and tracker blocking, from Brave's "
               "official apt repository.",
               user_action="install_brave_repo"),
    Component("gn_vivaldi", "Vivaldi", "Chromium-based power-user browser — tab stacking/tiling, built-in "
               "notes — from Vivaldi's official apt repository.",
               user_action="install_vivaldi_repo"),
    Component("gn_vlc", "VLC", "Plays essentially any video or audio file you throw at it.",
               packages=["vlc"], recommended=True),
    Component("gn_qbittorrent", "qBittorrent", "A torrent client, for anyone who wants one.",
               packages=["qbittorrent"]),
    Component("gn_flatpak", "Flatpak", "Sandboxed app format — several entries across this app (the Retro & "
               "Emulation section in particular) install through it.",
               packages=["flatpak"], recommended=True),
    Component("gn_snap_toggle", "Snap support", "Off by default on Griffin Linux; this turns it on if you "
               "specifically want it.",
               user_action="toggle_snap:on"),
]


# ---------------------------------------------------------------------------
# Diagnostics — definitions used by the diagnostics page checklist.
# Each id maps to a check function in diagnostics.py.
# ---------------------------------------------------------------------------

DIAGNOSTIC_CHECK_IDS = [
    ("vulkan", "Vulkan available"),
    ("vulkan32", "Vulkan 32-bit"),
    ("wine_installed", "Wine installed"),
    ("wine_prefix", "Wine prefix healthy"),
    ("dxvk", "DXVK active"),
    ("pipewire", "PipeWire detected"),
    ("gamemode", "GameMode active"),
    ("proton", "Proton detected"),
    ("vcrun", "VC runtime present"),
    ("gpu_driver", "GPU driver present"),
    ("hw_accel", "Hardware acceleration (VAAPI)"),
]
