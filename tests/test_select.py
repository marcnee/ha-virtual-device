"""Virtual selects translating between friendly options and control values."""

from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.virtual_device.const import (
    CONF_ACTION_SELECT,
    CONF_ID,
    CONF_NAME,
    CONF_OPTIONS,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
    CONF_VALUE_TEMPLATE,
)

from .conftest import SetupDevice

SOURCE = "sensor.heatpump_status"
ENTITY_ID = "select.heat_pump_mode"
STRIP_CODE = "{{ value.split(' - ', 1)[-1] }}"
CODES = "{{ {'In Betrieb': 18, 'Standby': 19}[option] }}"


def mode(**extra: object) -> dict[str, object]:
    return {
        CONF_ID: "mode",
        CONF_PLATFORM: "select",
        CONF_NAME: "Mode",
        CONF_SOURCE_ENTITY: SOURCE,
        CONF_OPTIONS: ["In Betrieb", "Standby"],
        CONF_VALUE_TEMPLATE: STRIP_CODE,
        **extra,
    }


async def test_select_shows_the_option_for_the_source_value(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - In Betrieb")

    await setup_device([mode()])

    state = hass.states.get(ENTITY_ID)
    assert state.state == "In Betrieb"
    assert state.attributes["options"] == ["In Betrieb", "Standby"]


async def test_select_follows_source_changes(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - In Betrieb")
    await setup_device([mode()])

    hass.states.async_set(SOURCE, "19 - Standby")
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY_ID).state == "Standby"


async def test_value_that_is_not_an_option_is_unknown(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "99 - Störung")

    await setup_device([mode()])

    assert hass.states.get(ENTITY_ID).state == STATE_UNKNOWN


async def test_selecting_an_option_sends_the_control_value(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    calls = async_mock_service(hass, "test", "set_mode")
    hass.states.async_set(SOURCE, "18 - In Betrieb")
    action = [{"action": "test.set_mode", "data": {"mode": CODES}}]
    await setup_device([mode(**{CONF_ACTION_SELECT: action})])

    await hass.services.async_call(
        "select", "select_option", {"entity_id": ENTITY_ID, "option": "Standby"}, blocking=True
    )

    assert len(calls) == 1
    assert calls[0].data == {"mode": 19}
