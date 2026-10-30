"""Keeps the running virtual entities in sync with the configuration, without reloading.

A change of a virtual device only stops and starts the entities whose definition changed.
Other entities and other devices keep running untouched.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import EntityPlatform, async_get_current_platform

from .changes import Definition, plan_changes
from .const import (
    CONF_ENTITIES,
    CONF_ID,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_PLATFORM,
    SUBENTRY_TYPE_DEVICE,
)
from .entity import VirtualEntity, make_unique_id

type EntityKey = tuple[str, str]  # (subentry ID of the device, ID of the entity definition)
type EntityFactory = Callable[[ConfigSubentry, dict[str, Any]], VirtualEntity]
type VirtualDeviceConfigEntry = ConfigEntry[EntityManager]


def _device_identity(subentry: ConfigSubentry) -> tuple[Any, ...]:
    """What the device of an entity is built from; entities are restarted when it changes."""
    return (subentry.title, subentry.data.get(CONF_MANUFACTURER), subentry.data.get(CONF_MODEL))


class EntityManager:
    """Starts and stops the virtual entities of all virtual devices of the service."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._entry = entry
        self._platforms: dict[str, tuple[EntityPlatform, EntityFactory]] = {}
        self._running: dict[EntityKey, Definition] = {}
        self._entities: dict[EntityKey, VirtualEntity] = {}
        self._lock = asyncio.Lock()

    def _wanted(self) -> dict[EntityKey, Definition]:
        return {
            (subentry.subentry_id, config[CONF_ID]): (_device_identity(subentry), config)
            for subentry in self._entry.subentries.values()
            if subentry.subentry_type == SUBENTRY_TYPE_DEVICE
            for config in subentry.data[CONF_ENTITIES]
        }

    async def async_register_platform(self, platform: str, factory: EntityFactory) -> None:
        """Called by every platform when it is set up: start its entities."""
        self._platforms[platform] = (async_get_current_platform(), factory)
        wanted = self._wanted()
        async with self._lock:
            await self._start(
                {
                    key
                    for key, (_, config) in wanted.items()
                    if config[CONF_PLATFORM] == platform and key not in self._running
                },
                wanted,
            )

    async def async_update(self) -> None:
        """Apply a changed configuration."""
        async with self._lock:
            wanted = self._wanted()
            stop, start = plan_changes(self._running, wanted)
            for key in stop:
                del self._running[key]
                await self._entities.pop(key).async_remove()
            self.remove_stale_registry_entries()
            await self._start(start, wanted)

    async def _start(self, keys: set[EntityKey], wanted: dict[EntityKey, Definition]) -> None:
        by_group: dict[tuple[str, str], list[VirtualEntity]] = {}
        for key in sorted(keys):
            subentry_id, _ = key
            config = dict(wanted[key][1])
            platform = config[CONF_PLATFORM]
            if platform not in self._platforms:
                continue
            _, factory = self._platforms[platform]
            entity = factory(self._entry.subentries[subentry_id], config)
            self._entities[key] = entity
            self._running[key] = wanted[key]
            by_group.setdefault((platform, subentry_id), []).append(entity)
        for (platform, subentry_id), entities in by_group.items():
            await self._platforms[platform][0].async_add_entities(
                entities, config_subentry_id=subentry_id
            )

    def remove_stale_registry_entries(self) -> None:
        """Delete registry entries of virtual entities that are no longer configured."""
        registry = er.async_get(self._hass)
        wanted = {
            (config[CONF_PLATFORM], make_unique_id(subentry_id, config[CONF_ID]))
            for (subentry_id, _), (_, config) in self._wanted().items()
        }
        for registered in er.async_entries_for_config_entry(registry, self._entry.entry_id):
            if (registered.domain, registered.unique_id) not in wanted:
                registry.async_remove(registered.entity_id)
