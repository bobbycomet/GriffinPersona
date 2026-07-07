"""
Griffin Persona — anti-cheat compatibility lookup.

Backed by the community-maintained AreWeAntiCheatYet project
(https://github.com/AreWeAntiCheatYet/AreWeAntiCheatYet), which tracks which
games' anti-cheat systems work under Linux/Wine/Proton. This module only
ever reads that public dataset and shows it back to the person — it does
not install, patch, or configure any anti-cheat component, matching the
"informational only" promise on the Gaming page.
"""

from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

DATA_URL = "https://raw.githubusercontent.com/AreWeAntiCheatYet/AreWeAntiCheatYet/master/games.json"
CACHE_PATH = Path.home() / ".cache" / "griffin-persona" / "awacy-games.json"
CACHE_TTL_SECONDS = 24 * 3600


@dataclass
class AntiCheatResult:
    name: str
    status: str           # e.g. "Supported", "Denied", "Planned", "Broken", "Running"
    anticheats: list[str]
    reference: str
    url: str


def _cache_is_fresh() -> bool:
    return CACHE_PATH.exists() and (time.time() - CACHE_PATH.stat().st_mtime) < CACHE_TTL_SECONDS


def _load_games(force_refresh: bool = False) -> list[dict]:
    if not force_refresh and _cache_is_fresh():
        try:
            return json.loads(CACHE_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    req = urllib.request.Request(DATA_URL, headers={"User-Agent": "griffin-persona"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read())
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(data))
    return data


def search(query: str, limit: int = 8, force_refresh: bool = False) -> list[AntiCheatResult]:
    """Case-insensitive substring search over game names/slugs."""
    games = _load_games(force_refresh=force_refresh)
    q = query.strip().lower()
    if not q:
        return []
    matches = [g for g in games if q in g.get("name", "").lower() or q in g.get("slug", "").lower()]
    matches.sort(key=lambda g: (not g.get("name", "").lower().startswith(q), g.get("name", "")))
    return [
        AntiCheatResult(
            name=g.get("name", ""),
            status=g.get("status", "Unknown"),
            anticheats=g.get("anticheats", []),
            reference=g.get("reference") or (g.get("notes", [[None]])[0][1] if g.get("notes") else ""),
            url=g.get("url", ""),
        )
        for g in matches[:limit]
    ]


def cache_age_description() -> str:
    if not CACHE_PATH.exists():
        return "Not downloaded yet."
    age_min = int((time.time() - CACHE_PATH.stat().st_mtime) / 60)
    if age_min < 60:
        return f"Data is {age_min} min old."
    return f"Data is {age_min // 60}h old."
