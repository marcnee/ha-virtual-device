"""Virtual sensors."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import VirtualEntity, entity_configs


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create the virtual sensors of a virtual device."""
    async_add_entities(
        VirtualSensor(entry, config) for config in entity_configs(entry, Platform.SENSOR)
    )


class VirtualSensor(VirtualEntity, SensorEntity):
    """A sensor showing the state of a source entity."""

    @callback
    def _apply(self, value: Any | None) -> None:
        self._attr_native_value = value
