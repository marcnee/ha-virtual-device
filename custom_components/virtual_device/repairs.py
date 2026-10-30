"""Repair flow: choose a new source for a virtual entity whose source does not exist."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.repairs import RepairsFlow
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import EntitySelector

from .const import CONF_ENTITIES, CONF_ID, CONF_NAME, CONF_SOURCE_ENTITY, DOMAIN
from .missing_sources import replace_source
from .source_exists import source_exists
from .source_issues import ATTR_CONFIG_ID, ATTR_SUBENTRY_ID


async def async_create_fix_flow(
    hass: HomeAssistant, issue_id: str, data: dict[str, str | int | float | None] | None
) -> RepairsFlow:
    """Called by the repairs integration for a fixable issue of this integration."""
    return SourceMissingFlow(str(data[ATTR_SUBENTRY_ID]), str(data[ATTR_CONFIG_ID]))


class SourceMissingFlow(RepairsFlow):
    """Asks for a new source and stores it in the definition of the virtual entity."""

    def __init__(self, subentry_id: str, config_id: str) -> None:
        self._subentry_id = subentry_id
        self._config_id = config_id

    def _find(self) -> tuple[ConfigEntry, ConfigSubentry, dict[str, Any]] | None:
        """The service, device and definition of the entity, if it still exists."""
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if (subentry := entry.subentries.get(self._subentry_id)) is None:
                continue
            for config in subentry.data[CONF_ENTITIES]:
                if config[CONF_ID] == self._config_id:
                    return entry, subentry, config
        return None

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """The repairs integration passes its own data to this step: go to the form."""
        return await self.async_step_source()

    async def async_step_source(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Choose the new source."""
        if (found := self._find()) is None:
            return self.async_abort(reason="entity_not_found")
        entry, subentry, config = found
        errors = {}
        if user_input is not None:
            if source_exists(self.hass, user_input[CONF_SOURCE_ENTITY]):
                entities = replace_source(
                    list(subentry.data[CONF_ENTITIES]),
                    self._config_id,
                    user_input[CONF_SOURCE_ENTITY],
                )
                self.hass.config_entries.async_update_subentry(
                    entry, subentry, data={**subentry.data, CONF_ENTITIES: entities}
                )
                return self.async_create_entry(data={})
            errors[CONF_SOURCE_ENTITY] = "source_not_found"
        return self.async_show_form(
            step_id="source",
            data_schema=vol.Schema({vol.Required(CONF_SOURCE_ENTITY): EntitySelector()}),
            description_placeholders={
                "device": subentry.title,
                "entity": config[CONF_NAME],
                "source": config[CONF_SOURCE_ENTITY],
            },
            errors=errors,
        )
