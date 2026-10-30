"""Virtual numbers forwarding set-value commands."""

from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.virtual_device.const import (
    CONF_ACTION_SET,
    CONF_ID,
    CONF_MAX,
    CONF_MIN,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
    CONF_STEP,
    CONF_UNIT,
    CONF_VALUE_TEMPLATE,
)

from .conftest import SetupDevice

SOURCE = "sensor.heatpump_target"
ENTITY_ID = "number.heat_pump_target"
SET_VALUE = [{"action": "test.set", "data": {"value": "{{ value }}"}}]


def target(**extra: object) -> dict[str, object]:
    return {
        CONF_ID: "target",
        CONF_PLATFORM: "number",
        CONF_NAME: "Target",
        CONF_SOURCE_ENTITY: SOURCE,
        **extra,
    }


async def test_number_follows_source_and_exposes_its_range(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "21.5")

    await setup_device([target(**{CONF_MIN: 10, CONF_MAX: 30, CONF_STEP: 0.5, CONF_UNIT: "°C"})])

    state = hass.states.get(ENTITY_ID)
    assert state.state == "21.5"
    assert state.attributes["min"] == 10
    assert state.attributes["max"] == 30
    assert state.attributes["step"] == 0.5
    assert state.attributes["unit_of_measurement"] == "°C"


async def test_number_uses_template_and_defaults(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - In Betrieb")

    await setup_device([target(**{CONF_VALUE_TEMPLATE: "{{ value.split(' - ')[0] }}"})])

    state = hass.states.get(ENTITY_ID)
    assert state.state == "18.0"
    assert (state.attributes["min"], state.attributes["max"], state.attributes["step"]) == (
        0,
        100,
        1,
    )


async def test_number_with_non_numeric_source_is_unknown(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "In Betrieb")

    await setup_device([target()])

    assert hass.states.get(ENTITY_ID).state == STATE_UNKNOWN


async def test_set_value_runs_the_action_with_the_value(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    calls = async_mock_service(hass, "test", "set")
    hass.states.async_set(SOURCE, "21.5")
    await setup_device([target(**{CONF_ACTION_SET: SET_VALUE})])

    await hass.services.async_call(
        "number", "set_value", {"entity_id": ENTITY_ID, "value": 23}, blocking=True
    )

    assert len(calls) == 1
    assert calls[0].data == {"value": 23.0}
