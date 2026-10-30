"""The entity definitions stored in the virtual devices of the service."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry

from .const import CONF_ENTITIES, CONF_ID, SUBENTRY_TYPE_DEVICE
from .missing_sources import EntityKey


def entity_configs(entry: ConfigEntry) -> dict[EntityKey, dict[str, Any]]:
    """The entity definitions of all virtual devices of the service."""
    return {
        (subentry.subentry_id, config[CONF_ID]): config
        for subentry in entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_TYPE_DEVICE
        for config in subentry.data[CONF_ENTITIES]
    }
