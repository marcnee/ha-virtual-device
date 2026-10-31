"""Pure logic: which sources of virtual entities are missing, and replacing one."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .const import CONF_EXTRA_SOURCES, CONF_ID, CONF_SOURCE_ENTITY

type EntityKey = tuple[str, str]  # (subentry ID of the device, ID of the entity definition)
type MissingSource = tuple[EntityKey, str]  # (entity, ID of the source entity that is missing)


def all_sources(config: Mapping[str, Any]) -> list[str]:
    """The source of an entity followed by its extra sources; empty without a source."""
    if not (source := config.get(CONF_SOURCE_ENTITY)):
        return []
    return [source, *config.get(CONF_EXTRA_SOURCES, [])]


def missing_sources(
    definitions: Mapping[EntityKey, Mapping[str, Any]], exists: Callable[[str], bool]
) -> set[MissingSource]:
    """The sources that do not exist, each with the entity that uses it."""
    return {
        (key, source)
        for key, config in definitions.items()
        for source in all_sources(config)
        if not exists(source)
    }


def _replaced(config: dict[str, Any], old: str, new: str) -> dict[str, Any]:
    """One definition with the source `old` replaced; an extra source is never listed twice."""
    replaced = dict(config)
    if config.get(CONF_SOURCE_ENTITY) == old:
        replaced[CONF_SOURCE_ENTITY] = new
    if CONF_EXTRA_SOURCES in config:
        extras = [new if source == old else source for source in config[CONF_EXTRA_SOURCES]]
        replaced[CONF_EXTRA_SOURCES] = list(dict.fromkeys(extras))
    return replaced


def replace_source(
    entities: list[dict[str, Any]], config_id: str, old: str, new: str
) -> list[dict[str, Any]]:
    """The entity definitions with the source `old` of one entity replaced by `new`."""
    return [
        _replaced(config, old, new) if config[CONF_ID] == config_id else config
        for config in entities
    ]
