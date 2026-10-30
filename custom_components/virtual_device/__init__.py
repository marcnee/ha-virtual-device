"""Virtual Device: bundle entities of different integrations into one device."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import CONF_ENTITIES, CONF_ID, CONF_PLATFORM, PLATFORMS
from .entity import make_unique_id


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a virtual device from a config entry."""
    _remove_stale_entities(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_on_update))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload_on_update(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Apply changed options by reloading the virtual device."""
    await hass.config_entries.async_reload(entry.entry_id)


def _remove_stale_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Delete registry entries of virtual entities that are no longer configured."""
    registry = er.async_get(hass)
    wanted = {
        (config[CONF_PLATFORM], make_unique_id(entry.entry_id, config[CONF_ID]))
        for config in entry.options[CONF_ENTITIES]
    }
    for registered in er.async_entries_for_config_entry(registry, entry.entry_id):
        if (registered.domain, registered.unique_id) not in wanted:
            registry.async_remove(registered.entity_id)
