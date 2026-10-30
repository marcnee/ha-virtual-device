"""Pure logic: actions suggested to forward commands of a virtual entity to its source."""

from __future__ import annotations

from typing import Any

from homeassistant.core import State

from .const import CONF_ACTION_OFF, CONF_ACTION_ON, CONF_ACTION_SELECT, CONF_ACTION_SET

# Sources that homeassistant.turn_on / turn_off can switch.
_SWITCHABLE = frozenset({"switch", "input_boolean", "light", "fan"})
_NUMBER = frozenset({"number", "input_number"})
_SELECT = frozenset({"select", "input_select"})

# Resolved when the action runs, so the action keeps working if the source is changed later.
_TARGET = {"entity_id": "{{ source_entity }}"}


def forwarding_actions(state: State | None) -> dict[str, list[dict[str, Any]]]:
    """Actions (by config key) that pass commands on to the source, if its domain allows it."""
    if state is None:
        return {}
    domain = state.domain
    if domain in _SWITCHABLE:
        return {
            CONF_ACTION_ON: [{"action": "homeassistant.turn_on", "target": dict(_TARGET)}],
            CONF_ACTION_OFF: [{"action": "homeassistant.turn_off", "target": dict(_TARGET)}],
        }
    if domain in _NUMBER:
        return {
            CONF_ACTION_SET: [
                {
                    "action": f"{domain}.set_value",
                    "target": dict(_TARGET),
                    "data": {"value": "{{ value }}"},
                }
            ]
        }
    if domain in _SELECT:
        return {
            CONF_ACTION_SELECT: [
                {
                    "action": f"{domain}.select_option",
                    "target": dict(_TARGET),
                    "data": {"option": "{{ option }}"},
                }
            ]
        }
    return {}
