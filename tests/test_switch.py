"""Virtual switches forwarding on/off commands."""

import pytest
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.virtual_device.const import (
    CONF_ACTION_OFF,
    CONF_ACTION_ON,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
    CONF_VALUE_TEMPLATE,
)

from .conftest import SetupDevice

SOURCE = "sensor.heatpump_mode"
ENTITY_ID = "switch.heat_pump_power"
TURN_ON = [{"action": "test.turn_on", "data": {"target": "{{ source_entity }}"}}]
TURN_OFF = [{"action": "test.turn_off"}]


def power(**extra: object) -> dict[str, object]:
    return {
        CONF_ID: "power",
        CONF_PLATFORM: "switch",
        CONF_NAME: "Power",
        CONF_SOURCE_ENTITY: SOURCE,
        **extra,
    }


async def test_switch_state_follows_source_through_template(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - In Betrieb")
    await setup_device([power(**{CONF_VALUE_TEMPLATE: "{{ value.startswith('18') }}"})])
    assert hass.states.get(ENTITY_ID).state == STATE_ON

    hass.states.async_set(SOURCE, "19 - Standby")
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY_ID).state == STATE_OFF


async def test_turn_on_runs_the_configured_action(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    calls = async_mock_service(hass, "test", "turn_on")
    hass.states.async_set(SOURCE, "off")
    await setup_device([power(**{CONF_ACTION_ON: TURN_ON, CONF_ACTION_OFF: TURN_OFF})])

    await hass.services.async_call("switch", "turn_on", {"entity_id": ENTITY_ID}, blocking=True)

    assert len(calls) == 1
    assert calls[0].data == {"target": SOURCE}


async def test_turn_off_runs_the_configured_action(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    calls = async_mock_service(hass, "test", "turn_off")
    hass.states.async_set(SOURCE, "on")
    await setup_device([power(**{CONF_ACTION_ON: TURN_ON, CONF_ACTION_OFF: TURN_OFF})])

    await hass.services.async_call("switch", "turn_off", {"entity_id": ENTITY_ID}, blocking=True)

    assert len(calls) == 1


async def test_state_only_changes_when_the_source_reports_it(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    async_mock_service(hass, "test", "turn_on")
    hass.states.async_set(SOURCE, "off")
    await setup_device([power(**{CONF_ACTION_ON: TURN_ON, CONF_ACTION_OFF: TURN_OFF})])

    await hass.services.async_call("switch", "turn_on", {"entity_id": ENTITY_ID}, blocking=True)
    assert hass.states.get(ENTITY_ID).state == STATE_OFF

    hass.states.async_set(SOURCE, "on")
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == STATE_ON


async def test_missing_action_raises_a_clear_error(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "off")
    await setup_device([power(**{CONF_ACTION_OFF: TURN_OFF})])

    with pytest.raises(HomeAssistantError, match="no action"):
        await hass.services.async_call("switch", "turn_on", {"entity_id": ENTITY_ID}, blocking=True)
