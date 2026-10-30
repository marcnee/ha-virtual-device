"""Options flow: add, edit and remove the entities of a virtual device.

Changes are collected in a working copy and only stored when "save" is chosen.
"""

from __future__ import annotations

import uuid
from copy import deepcopy
from typing import Any

import voluptuous as vol
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigFlowResult, OptionsFlow
from homeassistant.const import Platform
from homeassistant.helpers.selector import (
    ActionSelector,
    EntitySelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TemplateSelector,
    TextSelector,
    TextSelectorConfig,
)

from .const import (
    CONF_ACTION_OFF,
    CONF_ACTION_ON,
    CONF_ACTION_PRESS,
    CONF_ACTION_SELECT,
    CONF_ACTION_SET,
    CONF_DEVICE_CLASS,
    CONF_ENTITIES,
    CONF_ID,
    CONF_MAX,
    CONF_MIN,
    CONF_NAME,
    CONF_OPTIONS,
    CONF_PICK,
    CONF_PLATFORM,
    CONF_SOURCE_ATTRIBUTE,
    CONF_SOURCE_ENTITY,
    CONF_STATE_CLASS,
    CONF_STEP,
    CONF_UNIT,
    CONF_VALUE_TEMPLATE,
    PLATFORMS,
)

# Fields kept when the platform of an entity is changed while editing.
_SHARED_KEYS = {CONF_ID, CONF_SOURCE_ENTITY, CONF_SOURCE_ATTRIBUTE, CONF_VALUE_TEMPLATE}


def _suggest(draft: dict[str, Any], key: str) -> dict[str, Any]:
    """Prefill a form field from the entity being edited."""
    return {"suggested_value": draft.get(key)}


# Sensors with a device class need numbers, so classes for dates and enums are not offered.
_SENSOR_DEVICE_CLASSES = sorted(
    c.value
    for c in SensorDeviceClass
    if c not in {SensorDeviceClass.DATE, SensorDeviceClass.TIMESTAMP, SensorDeviceClass.ENUM}
)
_SENSOR_STATE_CLASSES = [c.value for c in SensorStateClass]


def _dropdown(options: list[str]) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN, sort=True)
    )


def _action_field(draft: dict[str, Any], key: str) -> dict[Any, Any]:
    return {vol.Optional(key, description=_suggest(draft, key)): ActionSelector()}


def _details_schema(platform: str, draft: dict[str, Any]) -> vol.Schema | None:
    """Platform specific fields, or None if the platform has none."""
    fields: dict[Any, Any]
    match platform:
        case Platform.SENSOR:
            fields = {
                vol.Optional(CONF_UNIT, description=_suggest(draft, CONF_UNIT)): TextSelector(),
                vol.Optional(
                    CONF_DEVICE_CLASS, description=_suggest(draft, CONF_DEVICE_CLASS)
                ): _dropdown(_SENSOR_DEVICE_CLASSES),
                vol.Optional(
                    CONF_STATE_CLASS, description=_suggest(draft, CONF_STATE_CLASS)
                ): _dropdown(_SENSOR_STATE_CLASSES),
            }
        case Platform.SWITCH:
            fields = _action_field(draft, CONF_ACTION_ON) | _action_field(draft, CONF_ACTION_OFF)
        case Platform.NUMBER:
            number = NumberSelector(NumberSelectorConfig(mode=NumberSelectorMode.BOX, step="any"))
            fields = {
                vol.Required(CONF_MIN, default=draft.get(CONF_MIN, 0)): number,
                vol.Required(CONF_MAX, default=draft.get(CONF_MAX, 100)): number,
                vol.Required(CONF_STEP, default=draft.get(CONF_STEP, 1)): number,
                vol.Optional(CONF_UNIT, description=_suggest(draft, CONF_UNIT)): TextSelector(),
            } | _action_field(draft, CONF_ACTION_SET)
        case Platform.SELECT:
            fields = {
                vol.Optional(CONF_OPTIONS, description=_suggest(draft, CONF_OPTIONS)): TextSelector(
                    TextSelectorConfig(multiple=True)
                )
            } | _action_field(draft, CONF_ACTION_SELECT)
        case Platform.BUTTON:
            fields = _action_field(draft, CONF_ACTION_PRESS)
        case _:
            return None
    return vol.Schema(fields)


def _validate_details(platform: str, user_input: dict[str, Any]) -> dict[str, str]:
    """Form errors for the platform specific fields."""
    errors: dict[str, str] = {}
    if platform == Platform.NUMBER and user_input[CONF_MIN] >= user_input[CONF_MAX]:
        errors[CONF_MAX] = "min_greater_max"
    if platform == Platform.SELECT and not user_input.get(CONF_OPTIONS):
        errors[CONF_OPTIONS] = "options_required"
    return errors


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

    # ---- remove / pick an entity ------------------------------------------------------------
    def _pick_options(self) -> list[SelectOptionDict]:
        return [
            SelectOptionDict(value=e[CONF_ID], label=f"{e[CONF_NAME]} ({e[CONF_PLATFORM]})")
            for e in self._working_copy
        ]

    async def async_step_remove_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Remove virtual entities (the source entities stay untouched)."""
        if user_input is not None:
            removed = set(user_input[CONF_PICK])
            self._entities = [e for e in self._working_copy if e[CONF_ID] not in removed]
            return await self.async_step_init()
        schema = vol.Schema(
            {
                vol.Required(CONF_PICK): SelectSelector(
                    SelectSelectorConfig(
                        options=self._pick_options(), multiple=True, mode=SelectSelectorMode.LIST
                    )
                )
            }
        )
        return self.async_show_form(step_id="remove_entity", data_schema=schema)

    async def async_step_edit_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose the entity to edit, then continue with its (prefilled) forms."""
        if user_input is not None:
            chosen = next(e for e in self._working_copy if e[CONF_ID] == user_input[CONF_PICK])
            self._draft = deepcopy(chosen)
            return self._show_basics_form()
        schema = vol.Schema(
            {
                vol.Required(CONF_PICK): SelectSelector(
                    SelectSelectorConfig(
                        options=self._pick_options(), mode=SelectSelectorMode.DROPDOWN
                    )
                )
            }
        )
        return self.async_show_form(step_id="edit_entity", data_schema=schema)

    # ---- add or edit an entity --------------------------------------------------------------
    async def async_step_add_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Platform and name."""
        if user_input is None:
            self._draft = {}
            return self._show_basics_form()
        platform = user_input[CONF_PLATFORM]
        if self._draft.get(CONF_PLATFORM, platform) != platform:
            # Platform changed while editing: keep only what all platforms share.
            self._draft = {k: v for k, v in self._draft.items() if k in _SHARED_KEYS}
        self._draft |= {CONF_PLATFORM: platform, CONF_NAME: user_input[CONF_NAME]}
        if platform == Platform.BUTTON:
            return await self.async_step_entity_details()
        return await self.async_step_entity_source()

    def _show_basics_form(self) -> ConfigFlowResult:
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_PLATFORM, default=self._draft.get(CONF_PLATFORM, Platform.SENSOR)
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=[str(p) for p in PLATFORMS],
                        mode=SelectSelectorMode.DROPDOWN,
                        translation_key="platform",
                    )
                ),
                vol.Required(CONF_NAME, default=self._draft.get(CONF_NAME, "")): TextSelector(),
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
        platform = self._draft[CONF_PLATFORM]
        schema = _details_schema(platform, self._draft)
        assert schema is not None
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _validate_details(platform, user_input)
            if not errors:
                self._merge(schema, user_input)
                self._commit_draft()
                return await self.async_step_init()
            self._draft |= user_input
            schema = _details_schema(platform, self._draft)
        return self.async_show_form(step_id="entity_details", data_schema=schema, errors=errors)
