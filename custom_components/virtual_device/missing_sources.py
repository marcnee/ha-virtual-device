"""Pure logic: which sources of virtual entities are missing, and replacing one."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .const import CONF_ID, CONF_SOURCE_ENTITY

type EntityKey = tuple[str, str]  # (subentry ID of the device, ID of the entity definition)


def missing_sources(
    definitions: Mapping[EntityKey, Mapping[str, Any]], exists: Callable[[str], bool]
) -> set[EntityKey]:
    """The entities whose configured source does not exist (entities without a source never)."""
    return {
        key
        for key, config in definitions.items()
        if (source := config.get(CONF_SOURCE_ENTITY)) and not exists(source)
    }


def replace_source(
    entities: list[dict[str, Any]], config_id: str, source: str
) -> list[dict[str, Any]]:
    """The entity definitions with the source of one entity replaced."""
    return [
        {**config, CONF_SOURCE_ENTITY: source} if config[CONF_ID] == config_id else config
        for config in entities
    ]
