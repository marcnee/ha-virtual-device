"""The release notes are the CHANGELOG section of the released version."""

import pytest

from scripts.release_notes import release_notes

CHANGELOG = """# Changelog

## [Unreleased]

- Something new

## [0.2.0] - 2026-11-01

### Added
- Feature B

## [0.1.0] - 2026-10-30

- Feature A
"""


def test_the_section_of_the_version_is_returned_without_its_heading() -> None:
    assert release_notes(CHANGELOG, "0.2.0") == "### Added\n- Feature B"


def test_the_last_section_runs_to_the_end() -> None:
    assert release_notes(CHANGELOG, "0.1.0") == "- Feature A"


def test_only_the_exact_version_matches() -> None:
    with pytest.raises(ValueError, match=r"version 0\.2$"):
        release_notes(CHANGELOG, "0.2")


def test_a_missing_version_is_an_error() -> None:
    with pytest.raises(ValueError, match=r"version 9\.9\.9"):
        release_notes(CHANGELOG, "9.9.9")


def test_an_empty_section_is_an_error() -> None:
    with pytest.raises(ValueError, match="is empty"):
        release_notes("## [1.0.0] - 2026-01-01\n\n## [0.9.0]\n- x\n", "1.0.0")
