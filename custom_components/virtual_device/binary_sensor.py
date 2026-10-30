"""Virtual binary sensors."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import VirtualEntity, add_platform_entities
from .transform import to_bool


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create the virtual binary sensors of a virtual device."""
    add_platform_entities(entry, Platform.BINARY_SENSOR, VirtualBinarySensor, async_add_entities)


class VirtualBinarySensor(VirtualEntity, BinarySensorEntity):
    """A binary sensor derived from a source entity."""

    @callback
    def _apply(self, value: Any | None) -> None:
        self._attr_is_on = None if value is None else to_bool(value)
