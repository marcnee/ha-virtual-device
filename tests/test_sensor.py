"""Virtual sensors."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.virtual_device.const import (
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
    DOMAIN,
)

from .conftest import SetupDevice

SOURCE = "sensor.heatpump_status"
STATUS = {
    CONF_ID: "status",
    CONF_PLATFORM: "sensor",
    CONF_NAME: "Status",
    CONF_SOURCE_ENTITY: SOURCE,
}


async def test_sensor_mirrors_source_state(hass: HomeAssistant, setup_device: SetupDevice) -> None:
    hass.states.async_set(SOURCE, "18 - In Betrieb")

    await setup_device([STATUS])

    assert hass.states.get("sensor.heat_pump_status").state == "18 - In Betrieb"


async def test_sensor_is_grouped_under_virtual_device(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - In Betrieb")

    entry = await setup_device([STATUS])

    entity = er.async_get(hass).async_get("sensor.heat_pump_status")
    device = dr.async_get(hass).async_get(entity.device_id)
    assert device.name == "Heat pump"
    assert (DOMAIN, entry.entry_id) in device.identifiers


async def test_source_entity_is_left_untouched(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - In Betrieb", {"foo": "bar"})

    await setup_device([STATUS])

    source = hass.states.get(SOURCE)
    assert source.state == "18 - In Betrieb"
    assert source.attributes == {"foo": "bar"}
