"""Setup, reload and unload of the service with its virtual devices."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.virtual_device.const import (
    CONF_ENTITIES,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
    DOMAIN,
)

from .conftest import SetupDevice, SetupDevices
from .helpers import subentry_by_title

SOURCE = "sensor.heatpump_status"


def sensor(entity_id: str, name: str) -> dict[str, str]:
    return {
        CONF_ID: entity_id,
        CONF_PLATFORM: "sensor",
        CONF_NAME: name,
        CONF_SOURCE_ENTITY: SOURCE,
    }


async def test_one_service_holds_several_devices(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    hass.states.async_set(SOURCE, "18")

    entry = await setup_devices(
        {"Heat pump": [sensor("a", "Status")], "Boiler": [sensor("a", "Status")]}
    )

    assert hass.states.get("sensor.heat_pump_status").state == "18"
    assert hass.states.get("sensor.boiler_status").state == "18"
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert {d.name for d in devices} == {"Heat pump", "Boiler"}
    for title in ("Heat pump", "Boiler"):
        subentry_id = subentry_by_title(entry, title).subentry_id
        device = dr.async_get(hass).async_get_device_by_identifier(
            (DOMAIN, subentry_id), entry.entry_id
        )
        assert device.name == title


async def test_changed_entities_create_new_entities(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18")
    entry = await setup_device([sensor("a", "Status")])

    hass.config_entries.async_update_subentry(
        entry,
        subentry_by_title(entry, "Heat pump"),
        data={CONF_ENTITIES: [sensor("a", "Status"), sensor("b", "Second")]},
    )
    await hass.async_block_till_done()

    assert hass.states.get("sensor.heat_pump_status").state == "18"
    assert hass.states.get("sensor.heat_pump_second").state == "18"


async def test_removed_entities_disappear_from_the_registry(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18")
    entry = await setup_device([sensor("a", "Status"), sensor("b", "Second")])

    hass.config_entries.async_update_subentry(
        entry, subentry_by_title(entry, "Heat pump"), data={CONF_ENTITIES: [sensor("a", "Status")]}
    )
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
    hass.config_entries.async_update_subentry(
        entry, subentry_by_title(entry, "Heat pump"), data={CONF_ENTITIES: [as_binary]}
    )
    await hass.async_block_till_done()

    assert hass.states.get("sensor.heat_pump_status") is None
    assert hass.states.get("binary_sensor.heat_pump_status").state == "on"


async def test_removing_a_device_removes_only_its_entities_and_device(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    hass.states.async_set(SOURCE, "18")
    entry = await setup_devices(
        {"Heat pump": [sensor("a", "Status")], "Boiler": [sensor("a", "Status")]}
    )
    boiler = subentry_by_title(entry, "Boiler")

    hass.config_entries.async_remove_subentry(entry, boiler.subentry_id)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.boiler_status") is None
    assert hass.states.get("sensor.heat_pump_status").state == "18"
    assert (
        dr.async_get(hass).async_get_device_by_identifier(
            (DOMAIN, boiler.subentry_id), entry.entry_id
        )
        is None
    )


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


async def test_old_entries_of_version_1_are_rejected_with_a_clear_message(
    hass: HomeAssistant, caplog
) -> None:
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(domain=DOMAIN, version=1, data={"device_name": "Old"})
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)

    assert entry.state is ConfigEntryState.MIGRATION_ERROR
    assert "delete this entry and add the virtual devices again" in caplog.text
