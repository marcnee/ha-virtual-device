"""Migration steps for the data of a virtual device (pure logic)."""

from itertools import pairwise
from typing import Any

from custom_components.virtual_device.config_flow import VirtualDeviceConfigFlow
from custom_components.virtual_device.migration import STEPS, Step, migrate_device_data


def add_marker(name: str):
    def migrate(data: dict[str, Any]) -> dict[str, Any]:
        return {**data, "markers": [*data.get("markers", []), name]}

    return migrate


FIRST = Step((2, 1), (2, 2), add_marker("first"))
SECOND = Step((2, 2), (2, 3), add_marker("second"))


def test_without_steps_the_data_stays_the_same() -> None:
    data = {"entities": [{"id": "a"}]}

    assert migrate_device_data(data, (2, 1), ()) == data


def test_steps_are_applied_in_order() -> None:
    result = migrate_device_data({"entities": []}, (2, 1), (SECOND, FIRST))

    assert result["markers"] == ["first", "second"]


def test_steps_that_were_already_applied_are_skipped() -> None:
    result = migrate_device_data({"entities": []}, (2, 2), (FIRST, SECOND))

    assert result["markers"] == ["second"]


def test_the_stored_data_is_not_modified() -> None:
    data = {"entities": []}

    migrate_device_data(data, (2, 1), (FIRST,))

    assert data == {"entities": []}


def test_the_steps_lead_to_the_current_version() -> None:
    """The steps follow each other without a gap and the last one reaches the current version."""
    current = (VirtualDeviceConfigFlow.VERSION, VirtualDeviceConfigFlow.MINOR_VERSION)
    versions = [(step.from_version, step.to_version) for step in STEPS]
    if not versions:
        return
    assert all(a[1] == b[0] for a, b in pairwise(versions))
    assert versions[-1][1] == current
