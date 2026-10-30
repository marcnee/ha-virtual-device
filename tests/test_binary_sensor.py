"""Virtual binary sensors."""

import pytest
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from custom_components.virtual_device.const import (
    CONF_DEVICE_CLASS,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
    CONF_VALUE_TEMPLATE,
)
from custom_components.virtual_device.transform import to_bool

from .conftest import SetupDevice

SOURCE = "sensor.heatpump_status"
ENTITY_ID = "binary_sensor.heat_pump_running"


def running(**extra: str) -> dict[str, str]:
    return {
        CONF_ID: "running",
        CONF_PLATFORM: "binary_sensor",
        CONF_NAME: "Running",
        CONF_SOURCE_ENTITY: SOURCE,
        **extra,
    }


@pytest.mark.parametrize("value", ["on", "On", "true", "True", "1", "yes"])
def test_to_bool_true(value: str) -> None:
    assert to_bool(value) is True


@pytest.mark.parametrize("value", ["off", "false", "0", "no", "anything"])
def test_to_bool_false(value: str) -> None:
    assert to_bool(value) is False


@pytest.mark.parametrize(("source", "expected"), [("on", STATE_ON), ("off", STATE_OFF)])
async def test_binary_sensor_interprets_source_state(
    hass: HomeAssistant, setup_device: SetupDevice, source: str, expected: str
) -> None:
    hass.states.async_set(SOURCE, source)

    await setup_device([running()])

    assert hass.states.get(ENTITY_ID).state == expected


async def test_binary_sensor_with_template_and_changes(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - In Betrieb")
    await setup_device([running(**{CONF_VALUE_TEMPLATE: "{{ value.startswith('18') }}"})])
    assert hass.states.get(ENTITY_ID).state == STATE_ON

    hass.states.async_set(SOURCE, "19 - Standby")
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY_ID).state == STATE_OFF


async def test_binary_sensor_unknown_and_unavailable(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, STATE_UNKNOWN)
    await setup_device([running()])
    assert hass.states.get(ENTITY_ID).state == STATE_UNKNOWN

    hass.states.async_set(SOURCE, STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == STATE_UNAVAILABLE


async def test_binary_sensor_has_the_configured_device_class(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "on")

    await setup_device([running(**{CONF_DEVICE_CLASS: "door"})])

    assert hass.states.get(ENTITY_ID).attributes["device_class"] == "door"


async def test_binary_sensor_without_device_class_has_none(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "on")

    await setup_device([running()])

    assert "device_class" not in hass.states.get(ENTITY_ID).attributes
