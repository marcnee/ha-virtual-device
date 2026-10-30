"""Repair issues for virtual entities whose source does not exist (Home Assistant glue)."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import (
    async_track_entity_registry_updated_event,
    async_track_state_change_event,
)
from homeassistant.helpers.start import async_at_started

from .const import CONF_NAME, CONF_SOURCE_ENTITY, DOMAIN
from .definitions import entity_configs
from .missing_sources import EntityKey, missing_sources
from .source_exists import source_exists

ISSUE_SOURCE_MISSING = "source_missing"
ATTR_SUBENTRY_ID = "subentry_id"
ATTR_CONFIG_ID = "config_id"


def issue_id(key: EntityKey) -> str:
    """The ID of the repair issue of one virtual entity."""
    return f"{ISSUE_SOURCE_MISSING}_{key[0]}_{key[1]}"


class SourceIssues:
    """Raises a repair issue for every virtual entity whose source does not exist.

    A source exists if it has a state or a registry entry (a disabled entity has no state).
    Nothing is checked before Home Assistant has started, since other integrations may still be
    setting up their entities.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._entry = entry
        self._started = False
        self._raised: set[EntityKey] = set()
        self._unsubscribe_start: Callable[[], None] | None = None
        self._unsubscribe_sources: list[Callable[[], None]] = []

    @callback
    def start(self) -> None:
        """Check as soon as Home Assistant has started."""
        self._unsubscribe_start = async_at_started(self._hass, self._on_started)

    @callback
    def stop(self) -> None:
        """Stop watching and remove the issues of this service."""
        if self._unsubscribe_start:
            self._unsubscribe_start()
        self._started = False
        self._unwatch()
        for key in self._raised:
            ir.async_delete_issue(self._hass, DOMAIN, issue_id(key))
        self._raised.clear()

    @callback
    def _on_started(self, hass: HomeAssistant) -> None:
        self._started = True
        self.update()

    @callback
    def update(self) -> None:
        """Raise issues for missing sources, remove those that are resolved, watch the sources."""
        if not self._started:
            return
        configs = entity_configs(self._entry)
        missing = missing_sources(configs, partial(source_exists, self._hass))
        for key in missing - self._raised:
            self._raise(key, configs[key])
        for key in self._raised - missing:
            ir.async_delete_issue(self._hass, DOMAIN, issue_id(key))
        self._raised = missing
        self._watch({c[CONF_SOURCE_ENTITY] for c in configs.values() if CONF_SOURCE_ENTITY in c})

    def _raise(self, key: EntityKey, config: dict[str, Any]) -> None:
        subentry = self._entry.subentries[key[0]]
        ir.async_create_issue(
            self._hass,
            DOMAIN,
            issue_id(key),
            is_fixable=True,
            severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE_SOURCE_MISSING,
            translation_placeholders={
                "device": subentry.title,
                "entity": config[CONF_NAME],
                "source": config[CONF_SOURCE_ENTITY],
            },
            data={ATTR_SUBENTRY_ID: key[0], ATTR_CONFIG_ID: key[1]},
        )

    def _watch(self, sources: set[str]) -> None:
        self._unwatch()
        if not sources:
            return
        entity_ids = sorted(sources)
        self._unsubscribe_sources = [
            async_track_state_change_event(self._hass, entity_ids, self._on_source_change),
            async_track_entity_registry_updated_event(
                self._hass, entity_ids, self._on_source_change
            ),
        ]

    def _unwatch(self) -> None:
        for unsubscribe in self._unsubscribe_sources:
            unsubscribe()
        self._unsubscribe_sources = []

    @callback
    def _on_source_change(self, event: Event[Any]) -> None:
        self.update()
