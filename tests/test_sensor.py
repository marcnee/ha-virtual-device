"""Virtual sensors."""

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
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


async def test_sensor_follows_source_changes(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - In Betrieb")
    await setup_device([STATUS])

    hass.states.async_set(SOURCE, "19 - Standby")
    await hass.async_block_till_done()

    assert hass.states.get("sensor.heat_pump_status").state == "19 - Standby"


async def test_sensor_is_unavailable_while_source_is_unavailable(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - In Betrieb")
    await setup_device([STATUS])

    hass.states.async_set(SOURCE, STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.heat_pump_status").state == STATE_UNAVAILABLE

    hass.states.async_set(SOURCE, "18 - In Betrieb")
    await hass.async_block_till_done()
    assert hass.states.get("sensor.heat_pump_status").state == "18 - In Betrieb"


async def test_sensor_is_unavailable_when_source_does_not_exist(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    await setup_device([STATUS])

    assert hass.states.get("sensor.heat_pump_status").state == STATE_UNAVAILABLE


async def test_sensor_is_unknown_while_source_is_unknown(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, STATE_UNKNOWN)

    await setup_device([STATUS])

    assert hass.states.get("sensor.heat_pump_status").state == STATE_UNKNOWN
