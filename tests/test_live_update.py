"""A configuration change only touches the entities it changes; nothing else is reloaded."""

from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState, ConfigSubentry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers import device_registry as dr

from custom_components.virtual_device.const import (
    CONF_ENTITIES,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
    CONF_VALUE_TEMPLATE,
    DOMAIN,
)

from .conftest import SetupDevices
from .helpers import subentry_by_title

SOURCE = "sensor.heatpump_status"


def sensor(config_id: str, name: str, **extra: str) -> dict[str, str]:
    return {
        CONF_ID: config_id,
        CONF_PLATFORM: "sensor",
        CONF_NAME: name,
        CONF_SOURCE_ENTITY: SOURCE,
    } | extra


def record_state_changes(hass: HomeAssistant) -> list[str]:
    """Entity IDs whose state was written or removed from now on."""
    changed: list[str] = []

    def collect(event: Event) -> None:
        changed.append(event.data["entity_id"])

    hass.bus.async_listen("state_changed", collect)
    return changed


async def edit(hass, entry, title: str, entities: list[dict[str, str]]) -> None:
    hass.config_entries.async_update_subentry(
        entry, subentry_by_title(entry, title), data={CONF_ENTITIES: entities}
    )
    await hass.async_block_till_done()


async def test_editing_a_device_does_not_reload_the_service(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    hass.states.async_set(SOURCE, "18")
    entry = await setup_devices({"Heat pump": [sensor("a", "Status")]})

    with patch.object(hass.config_entries, "async_reload") as reload:
        await edit(hass, entry, "Heat pump", [sensor("a", "Status"), sensor("b", "Second")])

    reload.assert_not_called()
    assert entry.state is ConfigEntryState.LOADED


async def test_other_devices_are_left_alone(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    hass.states.async_set(SOURCE, "18")
    entry = await setup_devices(
        {"Heat pump": [sensor("a", "Status")], "Boiler": [sensor("a", "Status")]}
    )
    changed = record_state_changes(hass)

    await edit(hass, entry, "Heat pump", [sensor("a", "Status"), sensor("b", "Second")])

    assert "sensor.heat_pump_second" in changed
    assert "sensor.boiler_status" not in changed
    assert hass.states.get("sensor.boiler_status").state == "18"


async def test_unchanged_entities_of_the_edited_device_are_left_alone(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    hass.states.async_set(SOURCE, "18")
    entry = await setup_devices({"Heat pump": [sensor("a", "Status"), sensor("b", "Second")]})
    changed = record_state_changes(hass)

    await edit(hass, entry, "Heat pump", [sensor("a", "Status"), sensor("b", "Second renamed")])

    assert "sensor.heat_pump_status" not in changed
    assert hass.states.get("sensor.heat_pump_status").state == "18"


async def test_a_changed_entity_follows_its_new_definition(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    hass.states.async_set(SOURCE, "18 - Running")
    entry = await setup_devices({"Heat pump": [sensor("a", "Status")]})
    assert hass.states.get("sensor.heat_pump_status").state == "18 - Running"

    template = "{{ value.split(' - ', 1)[-1] }}"
    await edit(hass, entry, "Heat pump", [sensor("a", "Status", **{CONF_VALUE_TEMPLATE: template})])

    assert hass.states.get("sensor.heat_pump_status").state == "Running"
    hass.states.async_set(SOURCE, "19 - Standby")
    await hass.async_block_till_done()
    assert hass.states.get("sensor.heat_pump_status").state == "Standby"


async def test_a_changed_entity_follows_the_source_only_once(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    hass.states.async_set(SOURCE, "18")
    entry = await setup_devices({"Heat pump": [sensor("a", "Status")]})
    await edit(hass, entry, "Heat pump", [{**sensor("a", "Status"), CONF_NAME: "Status 2"}])
    changed = record_state_changes(hass)

    hass.states.async_set(SOURCE, "19")
    await hass.async_block_till_done()

    assert (
        changed.count("sensor.heat_pump_status_2") + changed.count("sensor.heat_pump_status") == 1
    )


async def test_a_new_device_starts_without_touching_the_others(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    hass.states.async_set(SOURCE, "18")
    entry = await setup_devices({"Heat pump": [sensor("a", "Status")]})
    changed = record_state_changes(hass)

    hass.config_entries.async_add_subentry(
        entry,
        ConfigSubentry(
            data={CONF_ENTITIES: [sensor("a", "Status")]},
            subentry_type="device",
            title="Boiler",
            unique_id=None,
        ),
    )
    await hass.async_block_till_done()

    assert hass.states.get("sensor.boiler_status").state == "18"
    assert "sensor.heat_pump_status" not in changed


async def test_renaming_a_device_renames_it_in_the_registry(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    hass.states.async_set(SOURCE, "18")
    entry = await setup_devices({"Heat pump": [sensor("a", "Status")]})
    subentry = subentry_by_title(entry, "Heat pump")

    hass.config_entries.async_update_subentry(entry, subentry, title="Heater")
    await hass.async_block_till_done()

    device = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, subentry.subentry_id), entry.entry_id
    )
    assert device.name == "Heater"
