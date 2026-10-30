"""Virtual binary sensors."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import VirtualEntity, entity_configs
from .transform import to_bool


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create the virtual binary sensors of a virtual device."""
    async_add_entities(
        VirtualBinarySensor(entry, config)
        for config in entity_configs(entry, Platform.BINARY_SENSOR)
    )


class VirtualBinarySensor(VirtualEntity, BinarySensorEntity):
    """A binary sensor derived from a source entity."""

    @callback
    def _apply(self, value: Any | None) -> None:
        self._attr_is_on = None if value is None else to_bool(value)
