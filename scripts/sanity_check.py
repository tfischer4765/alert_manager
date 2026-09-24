#!/usr/bin/env python3
"""Guard the invariants that nothing else checks.

  - manifest.json's version disagreeing with the tag, so HACS offers a
    release that reports a different version once installed
  - a tag that does not sort above every earlier one, so HACS never offers it
  - the integration directory and the manifest domain diverging, which
    leaves the integration installed but unloadable
  - translations/en.json drifting from strings.json, so the UI shows texts
    that differ from the ones that were reviewed

Run it with no argument to check the working tree, or pass a tag to also
require that the tag agrees with the version:

    python scripts/sanity_check.py
    python scripts/sanity_check.py v0.2.0
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = "alert_manager"
INTEGRATION = ROOT / "custom_components" / DOMAIN

SEMVER = re.compile(
    r"^v?(?P<core>\d+\.\d+\.\d+)(?:-(?P<pre>[0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$"
)

checks: list[str] = []
problems: list[str] = []


def check(label: str, actual: object, expected: object) -> None:
    if actual == expected:
        checks.append(f"  ok   {label}: {actual}")
    else:
        problems.append(f"{label}: got {actual!r}, expected {expected!r}")


def version_key(version: str) -> tuple:
    """Sort key following SemVer precedence.

    Numeric per position, so v0.10.0 sorts above v0.9.0, and a pre-release
    sorts below its release, so v1.0.0 sorts above v1.0.0-rc1 -- both of which
    a naive compare gets wrong.
    """
    match = SEMVER.match(version)
    if match is None:
        raise ValueError(version)
    core = tuple(int(n) for n in match["core"].split("."))
    if match["pre"] is None:
        # A release outranks every pre-release of the same version.
        return (core, (1,))
    identifiers = tuple(
        (0, int(part), "") if part.isdigit() else (1, 0, part)
        for part in match["pre"].split(".")
    )
    return (core, (0, identifiers))


def previous_tags(exclude: str) -> list[str]:
    """Earlier version tags; empty outside a git checkout."""
    try:
        output = subprocess.run(
            ["git", "tag", "--list", "v*"],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    return [t for t in output.split() if t != exclude and SEMVER.match(t)]


def main(tag: str | None) -> int:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text())
    version = manifest.get("version")

    # --- versions -----------------------------------------------------------
    if not version or not SEMVER.match(version) or version.startswith("v"):
        problems.append(f"manifest.json: version {version!r} is not major.minor.patch")
    else:
        checks.append(f"  ok   manifest.json version: {version}")

    if tag:
        if not SEMVER.match(tag) or not tag.startswith("v"):
            problems.append(f"tag {tag!r} is not v<major>.<minor>.<patch>[-<suffix>]")
        else:
            # v1.2.3 and v1.0.0-rc.1 both map to the version without the v.
            check("tag matches manifest.json version", tag[1:], version)

            # The only versioning rule that can be checked mechanically: a tag
            # has to be greater than every tag before it. Whether a change
            # deserves a minor or a patch is a judgement call and stays one.
            if earlier := previous_tags(tag):
                latest = max(earlier, key=version_key)
                if version_key(tag) > version_key(latest):
                    checks.append(f"  ok   {tag} is newer than {latest}")
                else:
                    problems.append(
                        f"{tag} is not greater than the existing tag {latest}"
                    )

    # --- structure ----------------------------------------------------------
    check("manifest.json domain matches directory", manifest.get("domain"), DOMAIN)

    strings = json.loads((INTEGRATION / "strings.json").read_text())
    english = json.loads((INTEGRATION / "translations" / "en.json").read_text())
    if strings == english:
        checks.append("  ok   translations/en.json matches strings.json")
    else:
        problems.append(
            "translations/en.json differs from strings.json -- copy strings.json over it"
        )

    # --- report -------------------------------------------------------------
    print("\n".join(checks))
    if problems:
        print()
        for problem in problems:
            # Recognised by GitHub Actions and surfaced on the run summary.
            print(f"::error::{problem}")
        print(f"\n{len(problems)} problem(s) found.")
        return 1
    print(f"\nAll {len(checks)} checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
