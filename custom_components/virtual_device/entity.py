"""Base class for all virtual entities."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, EventStateChangedData, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_DEVICE_NAME, CONF_ID, CONF_NAME, CONF_SOURCE_ENTITY, DOMAIN


class VirtualEntity(Entity):
    """An entity that belongs to the virtual device and follows a source entity."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, config: dict[str, Any]) -> None:
        self._source: str = config[CONF_SOURCE_ENTITY]
        self._attr_name = config[CONF_NAME]
        self._attr_unique_id = f"{entry.entry_id}_{config[CONF_ID]}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data[CONF_DEVICE_NAME],
        )

    async def async_added_to_hass(self) -> None:
        """Follow the source entity."""
        self.async_on_remove(
            async_track_state_change_event(self.hass, [self._source], self._handle_source_event)
        )
        self._refresh()

    @callback
    def _handle_source_event(self, event: Event[EventStateChangedData]) -> None:
        self._refresh()
        self.async_write_ha_state()

    @callback
    def _refresh(self) -> None:
        """Derive availability and value from the current source state."""
        source_state = self.hass.states.get(self._source)
        self._attr_available = source_state is not None and source_state.state != STATE_UNAVAILABLE
        if self._attr_available:
            unknown = source_state.state == STATE_UNKNOWN
            self._apply(None if unknown else source_state.state)

    @callback
    def _apply(self, value: str | None) -> None:
        """Take over the source value (None = unknown). Implemented per platform."""
        raise NotImplementedError
