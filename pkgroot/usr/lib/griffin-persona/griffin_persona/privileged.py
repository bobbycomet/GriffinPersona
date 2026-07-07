"""
Griffin Persona — privileged-operation client.

The GUI never runs apt/dpkg/systemctl directly. Instead it serializes a
*request* describing exactly what should change, and hands it to
``griffin-persona-helper`` through ``pkexec``. PolicyKit authenticates the
user once (the policy uses ``auth_admin_keep`` for an active session, so a
user doing several changes in one sitting is not re-prompted for every
single one) and the helper itself re-validates the request against a fixed
allow-list before touching the system — the GUI is not trusted input.

Request shape (all keys required unless noted):
    {
        "action": "<verb>",
        "packages": ["pkg1", "pkg2", ...],   # for apt verbs
        "label": "human readable description for the rollback ledger"
    }

Response shape (always JSON on stdout):
    {
        "ok": true/false,
        "log": "combined stdout/stderr of everything that ran",
        "error": "short message if ok is false"
    }
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


def _resolve_helper_path() -> str:
    """
    Order of preference:
    1. GRIFFIN_PERSONA_HELPER env var, if set — explicit override, always wins.
    2. A path relative to this very package: <root>/helper/griffin-persona-helper,
       where <root> is whatever directory griffin_persona/ lives in. This is the
       same relative layout in BOTH the dev bundle (dev-bundle/{griffin_persona,helper}/)
       and the installed .deb (/usr/lib/griffin-persona/{griffin_persona,helper}/),
       so this works out of the box for dev-bundle users with no setup step at all.
    3. The hardcoded installed-system path, as a last-resort fallback.
    """
    override = os.environ.get("GRIFFIN_PERSONA_HELPER")
    if override:
        return override
    relative = Path(__file__).resolve().parent.parent / "helper" / "griffin-persona-helper"
    if relative.exists():
        return str(relative)
    return "/usr/lib/griffin-persona/griffin-persona-helper"


HELPER_PATH = _resolve_helper_path()


@dataclass
class HelperResult:
    ok: bool
    log: str = ""
    error: str = ""

    @classmethod
    def from_raw(cls, stdout: str, returncode: int, stderr: str) -> "HelperResult":
        if returncode in (126, 127):
            # pkexec uses 126/127 for several unrelated failure modes (target not
            # found, no polkit authority running, auth dismissed) — don't guess,
            # use whatever pkexec actually printed to stderr to tell them apart.
            stderr_l = (stderr or "").lower()
            if "error getting authority" in stderr_l or "could not connect" in stderr_l:
                return cls(ok=False, error="No PolicyKit authority is running on this system "
                                            "(common in containers/minimal installs) — "
                                            "privileged actions need a real desktop session.")
            if "no such file or directory" in stderr_l or "error accessing" in stderr_l:
                return cls(ok=False, error=f"The privileged helper wasn't found at {HELPER_PATH}. "
                                            f"{stderr.strip()}")
            if stderr.strip():
                return cls(ok=False, error=f"Authorization failed: {stderr.strip()}")
            return cls(ok=False, error="Authentication was cancelled or denied.")
        try:
            data = json.loads(stdout.strip().splitlines()[-1]) if stdout.strip() else {}
        except (json.JSONDecodeError, IndexError):
            data = {}
        if not data:
            return cls(ok=(returncode == 0), log=stdout, error=stderr if returncode else "")
        return cls(ok=bool(data.get("ok")), log=data.get("log", ""), error=data.get("error", ""))


def run_privileged(request: dict, timeout: int = 1800) -> HelperResult:
    """
    Run a single request through pkexec -> helper. Blocking call;
    callers should invoke this from a worker thread, never the UI thread.
    """
    if not Path(HELPER_PATH).exists():
        return HelperResult(
            ok=False,
            error=f"Can't find the privileged helper at {HELPER_PATH}. If you're running "
                  f"from a dev checkout, make sure helper/griffin-persona-helper sits next "
                  f"to griffin_persona/, or set GRIFFIN_PERSONA_HELPER explicitly.",
        )
    payload = json.dumps(request)
    try:
        proc = subprocess.run(
            ["pkexec", HELPER_PATH, payload],
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return HelperResult(ok=False, error="pkexec is not installed on this system.")
    except subprocess.TimeoutExpired:
        return HelperResult(ok=False, error="The operation timed out.")
    return HelperResult.from_raw(proc.stdout, proc.returncode, proc.stderr)


def run_privileged_streaming(request: dict, on_line):
    """
    Like run_privileged, but calls on_line(str) for every line of combined
    output as it arrives, for live log panes. Returns the final HelperResult.
    """
    if not Path(HELPER_PATH).exists():
        return HelperResult(
            ok=False,
            error=f"Can't find the privileged helper at {HELPER_PATH}. If you're running "
                  f"from a dev checkout, make sure helper/griffin-persona-helper sits next "
                  f"to griffin_persona/, or set GRIFFIN_PERSONA_HELPER explicitly.",
        )
    payload = json.dumps(request)
    try:
        proc = subprocess.Popen(
            ["pkexec", HELPER_PATH, payload],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError:
        return HelperResult(ok=False, error="pkexec is not installed on this system.")

    lines = []
    for line in iter(proc.stdout.readline, ""):
        lines.append(line)
        on_line(line.rstrip("\n"))
    proc.wait()
    full = "".join(lines)
    return HelperResult.from_raw(full, proc.returncode, full)
