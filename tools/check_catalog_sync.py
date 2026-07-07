#!/usr/bin/env python3
"""
check_catalog_sync.py — maintainer/CI tool, NOT shipped inside the .deb.

Run this after touching packages.py or catalog.json:

    PYTHONPATH=pkgroot/usr/lib/griffin-persona python3 tools/check_catalog_sync.py

It walks every Component in packages.py, collects every literal apt package
name and every repo_id/app_id referenced through PRIVILEGED_USER_ACTIONS,
and fails (exit 1) if any of them is missing from catalog.json's allow-list.

This is the concrete fix for "the helper's allow-list and packages.py have
to be kept in sync by hand": they still live in two different files for the
security reasons explained in catalog.json and in the helper's docstring
(the helper must not import live GUI code), but going out of sync is now a
build failure instead of a silent, hoped-for invariant.
"""

from __future__ import annotations

import sys

from griffin_persona import actions, catalog, packages


def collect_components() -> list[packages.Component]:
    comps: list[packages.Component] = []
    for group in packages.GPU_PROFILES.values():
        comps.extend(group)
    comps.extend(packages.NVIDIA_LAPTOP_COMPONENTS)
    comps.extend(packages.WIN_CORE)
    comps.extend(packages.WIN_RUNNERS)
    comps.extend(packages.WIN_RUNTIME_RECOMMENDED)
    comps.extend(packages.WIN_RUNTIME_OPTIONAL)
    comps.extend(packages.WIN_LAUNCHERS)
    comps.extend(packages.AUDIO_COMPONENTS)
    comps.extend(packages.GAMING_COMPONENTS)
    comps.extend(packages.CREATIVE_COMPONENTS)
    comps.extend(packages.GENERAL_COMPONENTS)
    comps.extend(packages.STORAGE_COMPONENTS)
    comps.extend(packages.DEV_COMPONENTS)
    comps.append(packages.VKMARK_COMPONENT)
    return comps


def main() -> int:
    allowed = catalog.allowed_packages()
    repos = catalog.repos()
    release_apps = catalog.release_apps()

    missing_packages: set[str] = set()
    missing_repos: set[str] = set()
    missing_apps: set[str] = set()

    for c in collect_components():
        for pkg in c.packages:
            if pkg not in allowed:
                missing_packages.add(pkg)
        if c.user_action and c.user_action in actions.PRIVILEGED_USER_ACTIONS:
            req = actions.PRIVILEGED_USER_ACTIONS[c.user_action]
            if "repo_id" in req and req["repo_id"] not in repos:
                missing_repos.add(req["repo_id"])
            if "app_id" in req and req["app_id"] not in release_apps:
                missing_apps.add(req["app_id"])

    problems = []
    if missing_packages:
        problems.append(f"Packages referenced in packages.py but missing from catalog.json: {sorted(missing_packages)}")
    if missing_repos:
        problems.append(f"repo_ids referenced but missing from catalog.json: {sorted(missing_repos)}")
    if missing_apps:
        problems.append(f"app_ids referenced but missing from catalog.json: {sorted(missing_apps)}")

    if problems:
        print("CATALOG OUT OF SYNC:")
        for p in problems:
            print(" -", p)
        return 1

    total_pkgs = sum(len(c.packages) for c in collect_components())
    print(f"OK: {total_pkgs} package references across {len(collect_components())} components "
          f"all present in catalog.json ({len(allowed)} allowed packages, "
          f"{len(repos)} repos, {len(release_apps)} release apps).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
