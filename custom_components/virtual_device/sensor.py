"""Virtual sensors."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ENTITIES, CONF_PLATFORM
from .entity import VirtualEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create the virtual sensors of a virtual device."""
    async_add_entities(
        VirtualSensor(entry, config)
        for config in entry.options[CONF_ENTITIES]
        if config[CONF_PLATFORM] == "sensor"
    )


class VirtualSensor(VirtualEntity, SensorEntity):
    """A sensor showing the state of a source entity."""

    @callback
    def _apply(self, value: Any | None) -> None:
        self._attr_native_value = value
