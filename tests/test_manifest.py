"""Rules of hassfest for manifest.json that are cheap to check here."""

import json
from pathlib import Path

MANIFEST_FILE = Path(__file__).parents[1] / "custom_components/virtual_device/manifest.json"


def test_manifest_keys_are_sorted_like_hassfest_wants_them() -> None:
    """domain, name, then alphabetical order."""
    keys = list(json.loads(MANIFEST_FILE.read_text()))

    assert keys[:2] == ["domain", "name"]
    assert keys[2:] == sorted(keys[2:])
