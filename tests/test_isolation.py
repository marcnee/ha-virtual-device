"""The integration stays within itself: nothing outside its own entities and devices changes."""

from typing import Any

from homeassistant.components.repairs import repairs_flow_manager
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.virtual_device.const import (
    CONF_COPY_ATTRIBUTES,
    CONF_ENTITIES,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
    COPY_ALL,
    DOMAIN,
    PLATFORMS,
)

from .conftest import SetupDevice

SOURCE = "sensor.outside_temperature"


def virtual_sensor(config_id: str, name: str) -> dict[str, Any]:
    return {
        CONF_ID: config_id,
        CONF_PLATFORM: "sensor",
        CONF_NAME: name,
        CONF_SOURCE_ENTITY: SOURCE,
        CONF_COPY_ATTRIBUTES: COPY_ALL,
    }


def add_foreign_source(hass: HomeAssistant) -> None:
    """A source of another integration, on its own device, customized by the user."""
    other = MockConfigEntry(domain="other")
    other.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=other.entry_id, identifiers={("other", "station")}, name="Weather station"
    )
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "sensor",
        "other",
        "temperature",
        suggested_object_id="outside_temperature",
        config_entry=other,
        device_id=device.id,
    )
    registry.async_update_entity(
        SOURCE, name="My name", icon="mdi:thermometer", hidden_by=er.RegistryEntryHider.USER
    )
    hass.states.async_set(SOURCE, "5", {"unit_of_measurement": "°C", "room": "Garden"})


def outside_view(hass: HomeAssistant) -> dict[str, Any]:
    """Everything that does not belong to Virtual Device."""
    entities = er.async_get(hass)
    devices = dr.async_get(hass)
    state = hass.states.get(SOURCE)
    return {
        "source_state": (state.state, dict(state.attributes)),
        "entities": {e.entity_id: e for e in entities.entities.values() if e.platform != DOMAIN},
        "devices": {d.id: d for d in devices.devices if all(i[0] != DOMAIN for i in d.identifiers)},
        "config_entries": {
            e.entry_id: (e.data, e.options, e.disabled_by)
            for e in hass.config_entries.async_entries()
            if e.domain != DOMAIN
        },
        "issues": {key: i for key, i in ir.async_get(hass).issues.items() if key[0] != DOMAIN},
        "services": {
            domain: set(names) for domain, names in hass.services.async_services().items()
        },
    }


async def test_setting_up_changing_and_removing_devices_leaves_everything_else_alone(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    # The entity components are part of every real system; loading them is not our doing.
    for platform in PLATFORMS:
        assert await async_setup_component(hass, platform, {})
    add_foreign_source(hass)
    before = outside_view(hass)

    entry = await setup_device([virtual_sensor("outside", "Outside")])
    assert hass.states.get("sensor.heat_pump_outside") is not None
    assert outside_view(hass) == before

    subentry = next(iter(entry.subentries.values()))
    data = {**subentry.data, CONF_ENTITIES: [virtual_sensor("garden", "Garden")]}
    hass.config_entries.async_update_subentry(entry, subentry, data=data)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.heat_pump_garden") is not None
    assert outside_view(hass) == before

    hass.config_entries.async_remove_subentry(entry, subentry.subentry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.heat_pump_garden") is None
    assert outside_view(hass) == before

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert outside_view(hass) == before


async def test_a_missing_source_and_its_repair_leave_everything_else_alone(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    for platform in PLATFORMS:
        assert await async_setup_component(hass, platform, {})
    assert await async_setup_component(hass, "repairs", {})
    add_foreign_source(hass)
    ir.async_create_issue(
        hass,
        "other",
        "foreign",
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="foreign",
    )
    before = outside_view(hass)

    entry = await setup_device([virtual_sensor("outside", "Outside") | {CONF_SOURCE_ENTITY: "x.y"}])
    assert [key[0] for key in ir.async_get(hass).issues if key[0] == DOMAIN] == [DOMAIN]
    assert outside_view(hass) == before

    subentry = next(iter(entry.subentries.values()))
    manager = repairs_flow_manager(hass)
    [(_, issue_id)] = [key for key in ir.async_get(hass).issues if key[0] == DOMAIN]
    result = await manager.async_init(DOMAIN, context={"issue_id": issue_id})
    await manager.async_configure(result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE})
    await hass.async_block_till_done()

    assert subentry.data[CONF_ENTITIES][0][CONF_SOURCE_ENTITY] == SOURCE
    assert hass.states.get("sensor.heat_pump_outside").state == "5"
    assert [key for key in ir.async_get(hass).issues if key[0] == DOMAIN] == []
    assert outside_view(hass) == before
