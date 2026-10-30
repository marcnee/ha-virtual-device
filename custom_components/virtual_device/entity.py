"""Base class for all virtual entities."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

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
