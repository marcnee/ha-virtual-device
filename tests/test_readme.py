"""The installation instructions must match how the release ZIP is built."""

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
README = (ROOT / "README.md").read_text()
INSTALLATION = re.search(r"^## Installation\n(.*?)^## ", README, re.S | re.M)[1]


def test_manual_installation_uses_the_release_zip_and_the_integration_folder() -> None:
    manual = INSTALLATION.split("**Manual")[1]

    assert "virtual_device.zip" in manual
    assert "config/custom_components/virtual_device" in manual
    assert "restart" in manual.lower()
    assert "Add integration" in manual


def test_the_zip_has_its_files_at_the_top_level_as_the_instructions_say() -> None:
    """So it has to be unpacked into a folder named virtual_device."""
    workflow = (ROOT / ".github/workflows/release.yaml").read_text()

    assert "cd custom_components/virtual_device && zip -r" in workflow
    assert "directly" in INSTALLATION
