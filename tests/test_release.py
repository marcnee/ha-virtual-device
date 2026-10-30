"""The release set-up (HACS ZIP asset) must stay consistent."""

import json
import re
from pathlib import Path

from scripts.release_notes import release_notes

ROOT = Path(__file__).parents[1]
MANIFEST = json.loads((ROOT / "custom_components/virtual_device/manifest.json").read_text())
HACS = json.loads((ROOT / "hacs.json").read_text())
RELEASE_WORKFLOW = (ROOT / ".github/workflows/release.yaml").read_text()


def test_manifest_version_is_semver() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", MANIFEST["version"])


def test_hacs_installs_the_release_zip() -> None:
    assert HACS["zip_release"] is True
    assert HACS["filename"] == "virtual_device.zip"


def test_release_workflow_publishes_that_zip_for_version_tags() -> None:
    assert HACS["filename"] in RELEASE_WORKFLOW
    assert 'tags: ["v*"]' in RELEASE_WORKFLOW
    assert "gh release create" in RELEASE_WORKFLOW


def test_release_workflow_runs_the_tests_first() -> None:
    assert "uses: ./.github/workflows/ci.yaml" in RELEASE_WORKFLOW
    assert "needs: test" in RELEASE_WORKFLOW
    assert "workflow_call" in (ROOT / ".github/workflows/ci.yaml").read_text()


def test_changelog_has_notes_for_the_manifest_version() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text()

    assert release_notes(changelog, MANIFEST["version"])


def test_release_workflow_uses_the_changelog_as_release_notes() -> None:
    assert "scripts/release_notes.py" in RELEASE_WORKFLOW
    assert "--notes-file" in RELEASE_WORKFLOW
