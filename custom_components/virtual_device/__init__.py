"""Virtual Device: bundle entities of different integrations into one device."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import PLATFORMS
from .manager import EntityManager, VirtualDeviceConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Reject entries of the unreleased one-entry-per-device layout."""
    if entry.version < 2:
        _LOGGER.error(
            "Virtual Device entry '%s' uses an outdated layout from before the first release: "
            "delete this entry and add the virtual devices again",
            entry.title,
        )
        return False
    return True


async def async_setup_entry(hass: HomeAssistant, entry: VirtualDeviceConfigEntry) -> bool:
    """Set up the service and start the entities of all its virtual devices."""
    entry.runtime_data = EntityManager(hass, entry)
    entry.runtime_data.remove_stale_registry_entries()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_apply_update))
    # Changes made while the platforms were still being set up.
    await entry.runtime_data.async_update()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: VirtualDeviceConfigEntry) -> bool:
    """Unload the service."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_apply_update(hass: HomeAssistant, entry: VirtualDeviceConfigEntry) -> None:
    """Apply changed virtual devices to the running entities; nothing is reloaded."""
    await entry.runtime_data.async_update()
