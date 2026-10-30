"""Describe the events of Virtual Device for the logbook (the activity list)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.logbook import (
    LOGBOOK_ENTRY_ENTITY_ID,
    LOGBOOK_ENTRY_MESSAGE,
    LOGBOOK_ENTRY_NAME,
)
from homeassistant.const import ATTR_ENTITY_ID, ATTR_NAME
from homeassistant.core import Event, HomeAssistant, callback

from .const import ATTR_COMMAND, ATTR_SOURCE_ENTITY, DOMAIN, EVENT_COMMAND_FORWARDED


@callback
def async_describe_events(
    hass: HomeAssistant,
    async_describe_event: Callable[[str, str, Callable[[Event], dict[str, Any]]], None],
) -> None:
    """Tell the logbook how to show a forwarded command, and what it caused."""

    @callback
    def describe_forwarded_command(event: Event) -> dict[str, Any]:
        data = event.data
        command = data[ATTR_COMMAND]
        if source := data.get(ATTR_SOURCE_ENTITY):
            message = f"forwarded the {command} command to {source}"
        else:
            message = f"ran the {command} action"
        return {
            LOGBOOK_ENTRY_NAME: data[ATTR_NAME],
            LOGBOOK_ENTRY_MESSAGE: message,
            LOGBOOK_ENTRY_ENTITY_ID: data[ATTR_ENTITY_ID],
        }

    async_describe_event(DOMAIN, EVENT_COMMAND_FORWARDED, describe_forwarded_command)
