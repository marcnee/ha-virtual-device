"""Devices stored by a released version keep working after every update.

`tests/released/<version>.json` freezes the stored layout of a release together with what the
user sees from it: unique IDs, entity IDs, states, attributes, the device and the commands. The
files are never edited after the release. When the layout changes, the migration has to keep
every one of them working; a failing test here means a breaking change for users.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState, ConfigSubentryData
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from custom_components.virtual_device.config_flow import VirtualDeviceConfigFlow
from custom_components.virtual_device.const import DOMAIN, SUBENTRY_TYPE_DEVICE
from custom_components.virtual_device.migration import STEPS, Step, Version

RELEASED = sorted(Path(__file__).parent.joinpath("released").glob("*.json"))


@pytest.fixture(params=RELEASED, ids=lambda path: path.stem)
def released(request: pytest.FixtureRequest) -> dict[str, Any]:
    return json.loads(request.param.read_text(encoding="utf-8"))


async def set_up_stored(hass: HomeAssistant, released: dict[str, Any]) -> MockConfigEntry:
    for entity_id, source in released["sources"].items():
        hass.states.async_set(entity_id, source["state"], source["attributes"])
    device = released["device"]
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=released["entry"]["version"],
        minor_version=released["entry"]["minor_version"],
        data={},
        subentries_data=[
            ConfigSubentryData(
                data=device["data"],
                subentry_type=SUBENTRY_TYPE_DEVICE,
                subentry_id=device["subentry_id"],
                title=device["title"],
                unique_id=None,
            )
        ],
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_the_stored_device_is_loaded_at_the_current_version(
    hass: HomeAssistant, released: dict[str, Any]
) -> None:
    entry = await set_up_stored(hass, released)

    assert entry.state is ConfigEntryState.LOADED
    assert (entry.version, entry.minor_version) == (
        VirtualDeviceConfigFlow.VERSION,
        VirtualDeviceConfigFlow.MINOR_VERSION,
    )


async def test_unique_ids_entity_ids_and_the_device_stay_the_same(
    hass: HomeAssistant, released: dict[str, Any]
) -> None:
    entry = await set_up_stored(hass, released)

    subentry_id = released["device"]["subentry_id"]
    registry = er.async_get(hass)
    for config_id, expected in released["expected"].items():
        domain = expected["entity_id"].split(".")[0]
        entity_id = registry.async_get_entity_id(domain, DOMAIN, f"{subentry_id}_{config_id}")
        assert entity_id == expected["entity_id"]
    device = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, subentry_id), entry.entry_id
    )
    assert device is not None
    assert device.name == released["device"]["title"]
    assert device.manufacturer == released["device"]["data"]["manufacturer"]
    assert device.model == released["device"]["data"]["model"]
    assert len(registry.entities) == len(released["expected"])


async def test_states_and_attributes_stay_the_same(
    hass: HomeAssistant, released: dict[str, Any]
) -> None:
    await set_up_stored(hass, released)

    for expected in released["expected"].values():
        state = hass.states.get(expected["entity_id"])
        assert state.state == expected["state"], expected["entity_id"]
        for name, value in expected["attributes"].items():
            assert state.attributes[name] == value, (expected["entity_id"], name)
        for name in expected.get("absent_attributes", []):
            assert name not in state.attributes, (expected["entity_id"], name)


async def test_commands_are_still_forwarded(hass: HomeAssistant, released: dict[str, Any]) -> None:
    calls = {
        command["calls"]: async_mock_service(hass, *command["calls"].split("."))
        for command in released["commands"]
    }
    await set_up_stored(hass, released)

    for command in released["commands"]:
        await hass.services.async_call(
            command["domain"],
            command["service"],
            {"entity_id": command["entity_id"], **command["data"]},
            blocking=True,
        )
        [call] = calls[command["calls"]]
        assert dict(call.data) == command["call_data"], command["calls"]


def reaches(version: Version, steps: tuple[Step, ...], current: Version) -> bool:
    """Whether the steps lead from `version` to `current` without a gap."""
    while version != current:
        step = next((step for step in steps if step.from_version == version), None)
        if step is None:
            return False
        version = step.to_version
    return True


def current_version() -> Version:
    return (VirtualDeviceConfigFlow.VERSION, VirtualDeviceConfigFlow.MINOR_VERSION)


def test_a_migration_path_leads_from_every_released_version_to_the_current_one(
    released: dict[str, Any],
) -> None:
    stored = (released["entry"]["version"], released["entry"]["minor_version"])

    assert reaches(stored, STEPS, current_version())


def test_a_raised_version_without_a_step_is_detected() -> None:
    with patch.object(VirtualDeviceConfigFlow, "MINOR_VERSION", 2):
        assert not reaches((2, 1), (), current_version())
