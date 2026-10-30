"""Setup, reload and unload of a virtual device."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.virtual_device.const import (
    CONF_ENTITIES,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
)

from .conftest import SetupDevice

SOURCE = "sensor.heatpump_status"


def sensor(entity_id: str, name: str) -> dict[str, str]:
    return {
        CONF_ID: entity_id,
        CONF_PLATFORM: "sensor",
        CONF_NAME: name,
        CONF_SOURCE_ENTITY: SOURCE,
    }


async def test_changed_options_create_new_entities(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18")
    entry = await setup_device([sensor("a", "Status")])

    hass.config_entries.async_update_entry(
        entry, options={CONF_ENTITIES: [sensor("a", "Status"), sensor("b", "Second")]}
    )
    await hass.async_block_till_done()

    assert hass.states.get("sensor.heat_pump_status").state == "18"
    assert hass.states.get("sensor.heat_pump_second").state == "18"


async def test_removed_entities_disappear_from_the_registry(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18")
    entry = await setup_device([sensor("a", "Status"), sensor("b", "Second")])

    hass.config_entries.async_update_entry(entry, options={CONF_ENTITIES: [sensor("a", "Status")]})
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    assert registry.async_get("sensor.heat_pump_status") is not None
    assert registry.async_get("sensor.heat_pump_second") is None
    assert hass.states.get("sensor.heat_pump_second") is None


async def test_entity_changing_platform_replaces_the_old_entity(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "on")
    entry = await setup_device([sensor("a", "Status")])

    as_binary = {**sensor("a", "Status"), CONF_PLATFORM: "binary_sensor"}
    hass.config_entries.async_update_entry(entry, options={CONF_ENTITIES: [as_binary]})
    await hass.async_block_till_done()

    assert hass.states.get("sensor.heat_pump_status") is None
    assert hass.states.get("binary_sensor.heat_pump_status").state == "on"


async def test_unload_and_removal(hass: HomeAssistant, setup_device: SetupDevice) -> None:
    hass.states.async_set(SOURCE, "18")
    entry = await setup_device([sensor("a", "Status")])

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert hass.states.get("sensor.heat_pump_status").state == STATE_UNAVAILABLE

    assert await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.heat_pump_status") is None
