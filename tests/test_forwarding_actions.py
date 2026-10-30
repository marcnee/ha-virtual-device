"""Actions suggested for forwarding commands to the source (pure logic)."""

from typing import Any

import pytest
from homeassistant.core import State

from custom_components.virtual_device.const import (
    CONF_ACTION_OFF,
    CONF_ACTION_ON,
    CONF_ACTION_SELECT,
    CONF_ACTION_SET,
)
from custom_components.virtual_device.forwarding import forwarding_actions

TARGET = {"entity_id": "{{ source_entity }}"}


def suggestions(entity_id: str) -> dict[str, Any]:
    return forwarding_actions(State(entity_id, "on"))


def test_no_source_gives_no_suggestions() -> None:
    assert forwarding_actions(None) == {}


@pytest.mark.parametrize("domain", ["switch", "input_boolean", "light", "fan"])
def test_on_off_sources_are_switched_through_home_assistant(domain: str) -> None:
    assert suggestions(f"{domain}.x") == {
        CONF_ACTION_ON: [{"action": "homeassistant.turn_on", "target": TARGET}],
        CONF_ACTION_OFF: [{"action": "homeassistant.turn_off", "target": TARGET}],
    }


@pytest.mark.parametrize("domain", ["number", "input_number"])
def test_number_sources_get_the_value_forwarded(domain: str) -> None:
    assert suggestions(f"{domain}.x") == {
        CONF_ACTION_SET: [
            {"action": f"{domain}.set_value", "target": TARGET, "data": {"value": "{{ value }}"}}
        ]
    }


@pytest.mark.parametrize("domain", ["select", "input_select"])
def test_select_sources_get_the_option_forwarded(domain: str) -> None:
    assert suggestions(f"{domain}.x") == {
        CONF_ACTION_SELECT: [
            {
                "action": f"{domain}.select_option",
                "target": TARGET,
                "data": {"option": "{{ option }}"},
            }
        ]
    }


@pytest.mark.parametrize("domain", ["sensor", "binary_sensor", "climate", "button"])
def test_sources_that_cannot_be_controlled_that_way_get_nothing(domain: str) -> None:
    assert suggestions(f"{domain}.x") == {}
