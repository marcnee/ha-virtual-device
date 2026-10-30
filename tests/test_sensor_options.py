"""Unit, device class and state class of virtual sensors."""

import pytest
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from custom_components.virtual_device.const import (
    CONF_DEVICE_CLASS,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
    CONF_STATE_CLASS,
    CONF_UNIT,
    CONF_VALUE_TEMPLATE,
)

from .conftest import SetupDevice

SOURCE = "sensor.heatpump_temperature"
ENTITY_ID = "sensor.heat_pump_temperature"


def temperature(**extra: str) -> dict[str, str]:
    return {
        CONF_ID: "temperature",
        CONF_PLATFORM: "sensor",
        CONF_NAME: "Temperature",
        CONF_SOURCE_ENTITY: SOURCE,
        **extra,
    }


async def test_unit_device_class_and_state_class_are_exposed(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "21.5")

    await setup_device(
        [
            temperature(
                **{
                    CONF_UNIT: "°C",
                    CONF_DEVICE_CLASS: "temperature",
                    CONF_STATE_CLASS: "measurement",
                }
            )
        ]
    )

    state = hass.states.get(ENTITY_ID)
    assert state.state == "21.5"
    assert state.attributes["unit_of_measurement"] == "°C"
    assert state.attributes["device_class"] == "temperature"
    assert state.attributes["state_class"] == "measurement"


async def test_numeric_value_is_extracted_by_template(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - In Betrieb")

    await setup_device(
        [temperature(**{CONF_UNIT: "°C", CONF_VALUE_TEMPLATE: "{{ value.split(' - ')[0] }}"})]
    )

    assert hass.states.get(ENTITY_ID).state == "18"


@pytest.mark.parametrize("config", [{CONF_UNIT: "°C"}, {CONF_STATE_CLASS: "measurement"}])
async def test_non_numeric_value_with_numeric_settings_is_unknown(
    hass: HomeAssistant,
    setup_device: SetupDevice,
    config: dict[str, str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    hass.states.async_set(SOURCE, "In Betrieb")

    await setup_device([temperature(**config)])

    assert hass.states.get(ENTITY_ID).state == STATE_UNKNOWN
    assert "not numeric" in caplog.text


async def test_text_sensor_without_numeric_settings_keeps_text(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "In Betrieb")

    await setup_device([temperature()])

    assert hass.states.get(ENTITY_ID).state == "In Betrieb"
