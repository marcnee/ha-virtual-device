"""Base class for all virtual entities."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN, Platform
from homeassistant.core import Event, EventStateChangedData, State, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_DEVICE_NAME,
    CONF_ENTITIES,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ATTRIBUTE,
    CONF_SOURCE_ENTITY,
    CONF_VALUE_TEMPLATE,
    DOMAIN,
)
from .transform import ValueTransformer


def entity_configs(entry: ConfigEntry, platform: Platform) -> list[dict[str, Any]]:
    """The virtual entity definitions of one platform."""
    return [c for c in entry.options[CONF_ENTITIES] if c[CONF_PLATFORM] == platform]


class VirtualEntity(Entity):
    """An entity that belongs to the virtual device and follows a source entity."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, config: dict[str, Any]) -> None:
        self._config = config
        self._source: str = config[CONF_SOURCE_ENTITY]
        self._attribute: str | None = config.get(CONF_SOURCE_ATTRIBUTE)
        self._transform: ValueTransformer | None = None
        self._attr_name = config[CONF_NAME]
        self._attr_unique_id = f"{entry.entry_id}_{config[CONF_ID]}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data[CONF_DEVICE_NAME],
        )

    async def async_added_to_hass(self) -> None:
        """Follow the source entity."""
        self._transform = ValueTransformer(
            self.hass, self._config.get(CONF_VALUE_TEMPLATE), str(self._attr_name)
        )
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
            self._apply(self._transform(self._raw_value(source_state), source_state))

    def _raw_value(self, source_state: State) -> Any | None:
        """The attribute or state of the source; None if it has no value."""
        if self._attribute:
            return source_state.attributes.get(self._attribute)
        return None if source_state.state == STATE_UNKNOWN else source_state.state

    @callback
    def _apply(self, value: Any | None) -> None:
        """Take over the source value (None = unknown). Implemented per platform."""
        raise NotImplementedError
