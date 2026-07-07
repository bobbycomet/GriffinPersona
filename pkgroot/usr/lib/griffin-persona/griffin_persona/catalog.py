"""
Griffin Persona — shared catalog loader (GUI side).

Both this module and the privileged helper load the exact same
``catalog.json`` (see that file's own comment for why this is safe: once
installed, it sits under /usr, root:root, mode 0644 — an unprivileged GUI
process, even a compromised one, cannot rewrite it).

This replaces what used to be two independently-hand-maintained Python
literals (one in packages.py-adjacent code, one inside the helper script).
There is now exactly one list of allowed packages/repos/release-apps, and
``tools/check_catalog_sync.py`` fails the build if anything in the UI
catalog (packages.py) references a package/action that isn't in this file.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

# Both the installed layout (/usr/lib/griffin-persona/{catalog.json,griffin_persona/})
# and the dev bundle (<repo>/{catalog.json,griffin_persona/}) put this file one
# directory above the package, so the same relative lookup works in both.
_CANDIDATES = [
    Path(__file__).resolve().parent.parent / "catalog.json",
    Path("/usr/lib/griffin-persona/catalog.json"),
]


@lru_cache(maxsize=1)
def load() -> dict:
    for path in _CANDIDATES:
        if path.exists():
            return json.loads(path.read_text())
    raise FileNotFoundError(
        "catalog.json not found next to griffin_persona/ or at /usr/lib/griffin-persona/catalog.json"
    )


def allowed_packages() -> set[str]:
    return set(load().get("allowed_packages", []))


def repos() -> dict:
    return load().get("repos", {})


def release_apps() -> dict:
    return load().get("release_apps", {})
