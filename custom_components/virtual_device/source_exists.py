"""Whether a source entity exists."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


def source_exists(hass: HomeAssistant, entity_id: str) -> bool:
    """An entity exists if it has a state or a registry entry (a disabled entity has no state)."""
    return (
        hass.states.get(entity_id) is not None
        or er.async_get(hass).async_get(entity_id) is not None
    )
