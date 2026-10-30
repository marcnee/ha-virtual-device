"""Options flow: add, edit and remove the entities of a virtual device.

Changes are collected in a working copy and only stored when "save" is chosen.
"""

from __future__ import annotations

import uuid
from copy import deepcopy
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlowResult, OptionsFlow
from homeassistant.const import Platform
from homeassistant.helpers.selector import (
    ActionSelector,
    EntitySelector,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TemplateSelector,
    TextSelector,
)

from .const import (
    CONF_ACTION_PRESS,
    CONF_ENTITIES,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ATTRIBUTE,
    CONF_SOURCE_ENTITY,
    CONF_VALUE_TEMPLATE,
    PLATFORMS,
)

# Fields kept when the platform of an entity is changed while editing.
_SHARED_KEYS = {CONF_ID, CONF_SOURCE_ENTITY, CONF_SOURCE_ATTRIBUTE, CONF_VALUE_TEMPLATE}


def _suggest(draft: dict[str, Any], key: str) -> dict[str, Any]:
    """Prefill a form field from the entity being edited."""
    return {"suggested_value": draft.get(key)}


def _details_schema(platform: str, draft: dict[str, Any]) -> vol.Schema | None:
    """Platform specific fields, or None if the platform has none."""
    if platform == Platform.BUTTON:
        return vol.Schema(
            {
                vol.Optional(
                    CONF_ACTION_PRESS, description=_suggest(draft, CONF_ACTION_PRESS)
                ): ActionSelector()
            }
        )
    return None


class VirtualDeviceOptionsFlow(OptionsFlow):
    """Manage the entities of a virtual device."""

    def __init__(self) -> None:
        self._entities: list[dict[str, Any]] | None = None
        self._draft: dict[str, Any] = {}

    @property
    def _working_copy(self) -> list[dict[str, Any]]:
        if self._entities is None:
            self._entities = deepcopy(list(self.config_entry.options[CONF_ENTITIES]))
        return self._entities

    def _merge(self, schema: vol.Schema, user_input: dict[str, Any]) -> None:
        """Take form input into the draft; fields that were cleared are removed."""
        for key in schema.schema:
            self._draft.pop(str(key), None)
        self._draft.update(user_input)

    def _commit_draft(self) -> None:
        draft = {k: v for k, v in self._draft.items() if v not in (None, "", [])}
        draft.setdefault(CONF_ID, uuid.uuid4().hex[:8])
        entities = self._working_copy
        for index, existing in enumerate(entities):
            if existing[CONF_ID] == draft[CONF_ID]:
                entities[index] = draft
                break
        else:
            entities.append(draft)
        self._draft = {}

    # ---- menu -----------------------------------------------------------------------------
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Main menu."""
        menu = ["add_entity"]
        if self._working_copy:
            menu += ["edit_entity", "remove_entity"]
        menu.append("save")
        return self.async_show_menu(step_id="init", menu_options=menu)

    async def async_step_save(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Store the working copy; the integration reloads afterwards."""
        return self.async_create_entry(title="", data={CONF_ENTITIES: self._working_copy})

    # ---- add an entity --------------------------------------------------------------------
    async def async_step_add_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Platform and name."""
        if user_input is not None:
            self._draft = {
                CONF_PLATFORM: user_input[CONF_PLATFORM],
                CONF_NAME: user_input[CONF_NAME],
            }
            if user_input[CONF_PLATFORM] == Platform.BUTTON:
                return await self.async_step_entity_details()
            return await self.async_step_entity_source()
        schema = vol.Schema(
            {
                vol.Required(CONF_PLATFORM, default=Platform.SENSOR): SelectSelector(
                    SelectSelectorConfig(
                        options=[str(p) for p in PLATFORMS],
                        mode=SelectSelectorMode.DROPDOWN,
                        translation_key="platform",
                    )
                ),
                vol.Required(CONF_NAME): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_entity", data_schema=schema)

    async def async_step_entity_source(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Source entity, source attribute and value template."""
        schema = self._source_schema()
        if user_input is not None:
            self._merge(schema, user_input)
            return await self._next_after_source()
        return self.async_show_form(step_id="entity_source", data_schema=schema)

    def _source_schema(self) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(
                    CONF_SOURCE_ENTITY, description=_suggest(self._draft, CONF_SOURCE_ENTITY)
                ): EntitySelector(),
                vol.Optional(
                    CONF_SOURCE_ATTRIBUTE, description=_suggest(self._draft, CONF_SOURCE_ATTRIBUTE)
                ): TextSelector(),
                vol.Optional(
                    CONF_VALUE_TEMPLATE, description=_suggest(self._draft, CONF_VALUE_TEMPLATE)
                ): TemplateSelector(),
            }
        )

    async def _next_after_source(self) -> ConfigFlowResult:
        if _details_schema(self._draft[CONF_PLATFORM], self._draft) is not None:
            return await self.async_step_entity_details()
        self._commit_draft()
        return await self.async_step_init()

    async def async_step_entity_details(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Platform specific settings, such as the actions forwarding commands."""
        schema = _details_schema(self._draft[CONF_PLATFORM], self._draft)
        assert schema is not None
        if user_input is not None:
            self._merge(schema, user_input)
            self._commit_draft()
            return await self.async_step_init()
        return self.async_show_form(step_id="entity_details", data_schema=schema)
