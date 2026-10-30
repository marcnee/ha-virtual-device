"""Virtual Device: bundle entities of different integrations into one device."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import migration
from .config_flow import VirtualDeviceConfigFlow
from .const import PLATFORMS, SUBENTRY_TYPE_DEVICE
from .manager import EntityManager, VirtualDeviceConfigEntry
from .migration import migrate_device_data

_LOGGER = logging.getLogger(__name__)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Bring the data of all virtual devices to the current layout (see migration.py)."""
    if entry.version < 2:
        _LOGGER.error(
            "Virtual Device entry '%s' uses an outdated layout from before the first release: "
            "delete this entry and add the virtual devices again",
            entry.title,
        )
        return False
    version = (entry.version, entry.minor_version)
    # Migrate everything first, so that a failure leaves the stored data untouched.
    try:
        migrated = {
            subentry.subentry_id: migrate_device_data(subentry.data, version, migration.STEPS)
            for subentry in entry.subentries.values()
            if subentry.subentry_type == SUBENTRY_TYPE_DEVICE
        }
    except Exception:
        _LOGGER.exception("Migrating '%s' from version %s.%s failed", entry.title, *version)
        return False
    for subentry_id, data in migrated.items():
        hass.config_entries.async_update_subentry(entry, entry.subentries[subentry_id], data=data)
    hass.config_entries.async_update_entry(
        entry,
        version=VirtualDeviceConfigFlow.VERSION,
        minor_version=VirtualDeviceConfigFlow.MINOR_VERSION,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: VirtualDeviceConfigEntry) -> bool:
    """Set up the service and start the entities of all its virtual devices."""
    entry.runtime_data = EntityManager(hass, entry)
    entry.runtime_data.remove_stale_registry_entries()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_apply_update))
    # Changes made while the platforms were still being set up.
    await entry.runtime_data.async_update()
    entry.runtime_data.issues.start()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: VirtualDeviceConfigEntry) -> bool:
    """Unload the service."""
    entry.runtime_data.issues.stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_apply_update(hass: HomeAssistant, entry: VirtualDeviceConfigEntry) -> None:
    """Apply changed virtual devices to the running entities; nothing is reloaded."""
    await entry.runtime_data.async_update()
