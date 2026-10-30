"""Manufacturer and model of a virtual device in the device registry."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from custom_components.virtual_device.const import (
    CONF_ENTITIES,
    CONF_ID,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
    DOMAIN,
)

from .conftest import SetupDevices
from .helpers import subentry_by_title

SOURCE = "sensor.heatpump_status"
STATUS = {CONF_ID: "a", CONF_PLATFORM: "sensor", CONF_NAME: "Status", CONF_SOURCE_ENTITY: SOURCE}


def device_of(hass: HomeAssistant, entry, title: str) -> dr.DeviceEntry:
    subentry_id = subentry_by_title(entry, title).subentry_id
    return dr.async_get(hass).async_get_device_by_identifier((DOMAIN, subentry_id), entry.entry_id)


async def set_up(hass: HomeAssistant, setup_devices: SetupDevices, **device: str):
    """A service with the device "Heat pump" that has the given manufacturer and/or model."""
    hass.states.async_set(SOURCE, "18")
    entry = await setup_devices({"Heat pump": [STATUS]})
    if device:
        hass.config_entries.async_update_subentry(
            entry,
            subentry_by_title(entry, "Heat pump"),
            data={CONF_ENTITIES: [STATUS]} | device,
        )
        await hass.async_block_till_done()
    return entry


async def test_a_device_without_manufacturer_and_model_has_none(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    entry = await set_up(hass, setup_devices)

    device = device_of(hass, entry, "Heat pump")
    assert device.manufacturer is None
    assert device.model is None


async def test_manufacturer_and_model_are_shown_on_the_device(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    entry = await set_up(hass, setup_devices, **{CONF_MANUFACTURER: "Viessmann", CONF_MODEL: "V1"})

    device = device_of(hass, entry, "Heat pump")
    assert device.manufacturer == "Viessmann"
    assert device.model == "V1"


async def test_changing_and_clearing_them_updates_the_device_without_a_reload(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    entry = await set_up(hass, setup_devices, **{CONF_MANUFACTURER: "Viessmann", CONF_MODEL: "V1"})
    subentry = subentry_by_title(entry, "Heat pump")

    hass.config_entries.async_update_subentry(
        entry, subentry, data={CONF_ENTITIES: [STATUS], CONF_MODEL: "V2"}
    )
    await hass.async_block_till_done()

    device = device_of(hass, entry, "Heat pump")
    assert device.manufacturer is None
    assert device.model == "V2"
    assert hass.states.get("sensor.heat_pump_status").state == "18"
