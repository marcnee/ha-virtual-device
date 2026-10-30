"""Print the CHANGELOG.md section of a version, to be used as the notes of a GitHub release.

Usage: python scripts/release_notes.py 0.1.0
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CHANGELOG = Path(__file__).parents[1] / "CHANGELOG.md"


def release_notes(changelog: str, version: str) -> str:
    """The text under the heading `## [version]`, up to the next `## ` heading."""
    heading = re.compile(rf"^## \[{re.escape(version)}\](?:\s.*)?$", re.MULTILINE)
    match = heading.search(changelog)
    if match is None:
        raise ValueError(f"CHANGELOG.md has no section for version {version}")
    rest = changelog[match.end() :]
    next_heading = re.search(r"^## ", rest, re.MULTILINE)
    notes = (rest[: next_heading.start()] if next_heading else rest).strip()
    if not notes:
        raise ValueError(f"The CHANGELOG.md section for version {version} is empty")
    return notes


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        print(release_notes(CHANGELOG.read_text(), argv[0]))
    except ValueError as err:
        print(err, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
