"""Config entries of an older version are migrated when Home Assistant starts.

Pattern for the migration of a future release: store data in the old layout in a
`MockConfigEntry` with the old version, patch the new version and the steps, set the entry up
and check the migrated data.
"""

from typing import Any
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState, ConfigSubentryData
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.virtual_device.config_flow import VirtualDeviceConfigFlow
from custom_components.virtual_device.const import CONF_ENTITIES, DOMAIN, SUBENTRY_TYPE_DEVICE
from custom_components.virtual_device.migration import Step

from .helpers import subentry_by_title

SOURCE = "sensor.heatpump_status"


def rename_label_to_name(data: dict[str, Any]) -> dict[str, Any]:
    """A made-up change: entity definitions used "label" in version 2.1 and "name" from 2.2."""
    entities = [
        {("name" if k == "label" else k): v for k, v in e.items()} for e in data[CONF_ENTITIES]
    ]
    return {**data, CONF_ENTITIES: entities}


def fail(data: dict[str, Any]) -> dict[str, Any]:
    raise ValueError("cannot migrate")


def device(title: str, label: str) -> ConfigSubentryData:
    entity = {"id": "a", "platform": "sensor", "label": label, "source_entity": SOURCE}
    return ConfigSubentryData(
        data={CONF_ENTITIES: [entity]},
        subentry_type=SUBENTRY_TYPE_DEVICE,
        title=title,
        unique_id=None,
    )


def old_entry(hass: HomeAssistant, *titles: str) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        minor_version=1,
        data={},
        subentries_data=[device(title, f"{title} status") for title in titles],
    )
    entry.add_to_hass(hass)
    return entry


async def set_up_as_next_minor_version(hass: HomeAssistant, entry: MockConfigEntry, *steps: Step):
    with (
        patch.object(VirtualDeviceConfigFlow, "MINOR_VERSION", 2),
        patch("custom_components.virtual_device.migration.STEPS", steps),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()


async def test_the_data_of_every_device_is_migrated_and_the_version_raised(
    hass: HomeAssistant,
) -> None:
    hass.states.async_set(SOURCE, "18")
    entry = old_entry(hass, "Heat pump", "Boiler")

    await set_up_as_next_minor_version(hass, entry, Step((2, 1), (2, 2), rename_label_to_name))

    assert entry.state is ConfigEntryState.LOADED
    assert (entry.version, entry.minor_version) == (2, 2)
    for title in ("Heat pump", "Boiler"):
        [entity] = subentry_by_title(entry, title).data[CONF_ENTITIES]
        assert entity["name"] == f"{title} status"
        assert "label" not in entity
    assert hass.states.get("sensor.heat_pump_heat_pump_status").state == "18"


async def test_a_failing_step_changes_nothing(hass: HomeAssistant) -> None:
    """Not even the devices that were migrated before the failure, so a retry starts clean."""
    entry = old_entry(hass, "Heat pump", "Boiler")

    def fail_on_boiler(data: dict[str, Any]) -> dict[str, Any]:
        if data[CONF_ENTITIES][0]["label"].startswith("Boiler"):
            return fail(data)
        return rename_label_to_name(data)

    await set_up_as_next_minor_version(hass, entry, Step((2, 1), (2, 2), fail_on_boiler))

    assert entry.state is ConfigEntryState.MIGRATION_ERROR
    assert (entry.version, entry.minor_version) == (2, 1)
    [entity] = subentry_by_title(entry, "Heat pump").data[CONF_ENTITIES]
    assert "label" in entity
