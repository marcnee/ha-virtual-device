"""Forwarded commands show up in the activity list (logbook), with the virtual entity as cause."""

from collections.abc import Callable
from typing import Any

from homeassistant.auth.models import User
from homeassistant.const import ATTR_ENTITY_ID, ATTR_NAME
from homeassistant.core import Context, Event, HomeAssistant
from pytest_homeassistant_custom_component.common import async_capture_events, async_mock_service

from custom_components.virtual_device import logbook
from custom_components.virtual_device.const import (
    ATTR_COMMAND,
    ATTR_SOURCE_ENTITY,
    CONF_ACTION_ON,
    CONF_ACTION_PRESS,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
    EVENT_COMMAND_FORWARDED,
)

from .conftest import SetupDevice

SOURCE = "switch.heatpump"
ENTITY_ID = "switch.heat_pump_power"
TURN_ON = [{"action": "test.turn_on"}]


def describe(data: dict[str, Any]) -> dict[str, Any]:
    """What the logbook shows for a forwarded command with this event data."""
    registered: dict[str, Callable[[Event], dict[str, Any]]] = {}
    hass = None  # the platform does not use it

    logbook.async_describe_events(
        hass, lambda domain, event_type, describe: registered.update({event_type: describe})
    )
    return registered[EVENT_COMMAND_FORWARDED](Event(EVENT_COMMAND_FORWARDED, data))


def test_the_event_is_described_for_the_logbook() -> None:
    described = describe(
        {
            ATTR_NAME: "Heat pump Power",
            ATTR_ENTITY_ID: ENTITY_ID,
            ATTR_COMMAND: "on",
            ATTR_SOURCE_ENTITY: SOURCE,
        }
    )

    assert described == {
        "name": "Heat pump Power",
        "message": f"forwarded the on command to {SOURCE}",
        "entity_id": ENTITY_ID,
    }


def test_a_command_without_a_source_is_described_without_it() -> None:
    described = describe(
        {ATTR_NAME: "Heat pump Reset", ATTR_ENTITY_ID: "button.x", "command": "press"}
    )

    assert described["message"] == "ran the press action"


async def test_a_forwarded_command_is_announced_and_its_action_runs_in_a_child_context(
    hass: HomeAssistant, setup_device: SetupDevice, hass_admin_user: User
) -> None:
    calls = async_mock_service(hass, "test", "turn_on")
    events = async_capture_events(hass, EVENT_COMMAND_FORWARDED)
    hass.states.async_set(SOURCE, "off")
    await setup_device(
        [
            {
                CONF_ID: "power",
                CONF_PLATFORM: "switch",
                CONF_NAME: "Power",
                CONF_SOURCE_ENTITY: SOURCE,
                CONF_ACTION_ON: TURN_ON,
            }
        ]
    )
    command = Context(user_id=hass_admin_user.id)

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": ENTITY_ID}, blocking=True, context=command
    )

    assert len(events) == 1
    (event,) = events
    assert event.data == {
        ATTR_NAME: "Heat pump Power",
        ATTR_ENTITY_ID: ENTITY_ID,
        ATTR_COMMAND: "on",
        ATTR_SOURCE_ENTITY: SOURCE,
    }
    assert event.context.parent_id == command.id
    assert event.context.user_id == hass_admin_user.id
    # Whatever the action changes at the source belongs to this event.
    assert calls[0].context.id == event.context.id


async def test_a_command_without_a_source_is_announced_too(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    async_mock_service(hass, "test", "press")
    events = async_capture_events(hass, EVENT_COMMAND_FORWARDED)
    await setup_device(
        [
            {
                CONF_ID: "reset",
                CONF_PLATFORM: "button",
                CONF_NAME: "Reset",
                CONF_ACTION_PRESS: [{"action": "test.press"}],
            }
        ]
    )

    await hass.services.async_call(
        "button", "press", {"entity_id": "button.heat_pump_reset"}, blocking=True
    )

    assert [e.data for e in events] == [
        {
            ATTR_NAME: "Heat pump Reset",
            ATTR_ENTITY_ID: "button.heat_pump_reset",
            ATTR_COMMAND: "press",
        }
    ]
