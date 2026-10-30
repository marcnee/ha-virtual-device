"""Subentry flow: create a virtual device, or add, edit and remove its entities.

Changes are collected in a working copy and only stored when "save" is chosen.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from copy import deepcopy
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import SOURCE_RECONFIGURE, ConfigSubentryFlow, SubentryFlowResult
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.selector import (
    ActionSelector,
    EntitySelector,
    IconSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    ObjectSelector,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TemplateSelector,
    TextSelector,
    TextSelectorConfig,
)
from homeassistant.helpers.template import Template

from .attributes import RESERVED_ATTRIBUTES, attribute_template_error
from .const import (
    CONF_ACTION_OFF,
    CONF_ACTION_ON,
    CONF_ACTION_PRESS,
    CONF_ACTION_SELECT,
    CONF_ACTION_SET,
    CONF_ATTRIBUTE_NAMES,
    CONF_ATTRIBUTE_TEMPLATES,
    CONF_COPY_ATTRIBUTES,
    CONF_DEVICE_CLASS,
    CONF_DEVICE_NAME,
    CONF_ENTITIES,
    CONF_ICON,
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
    COPY_MODES,
    COPY_SELECTED,
    PLATFORMS,
)
from .forwarding import forwarding_actions
from .sensor_classes import SENSOR_DEVICE_CLASSES, SENSOR_STATE_CLASSES
from .source_defaults import defaults_from_source

# Fields kept when the platform of an entity is changed while editing.
_SOURCE_KEYS = (
    CONF_SOURCE_ENTITY,
    CONF_SOURCE_ATTRIBUTE,
    CONF_VALUE_TEMPLATE,
    CONF_COPY_ATTRIBUTES,
    CONF_ATTRIBUTE_NAMES,
    CONF_ATTRIBUTE_TEMPLATES,
)
_SHARED_KEYS = {CONF_ID, CONF_ICON, *_SOURCE_KEYS}


def _suggest(draft: dict[str, Any], key: str) -> dict[str, Any]:
    """Prefill a form field from the entity being edited."""
    return {"suggested_value": draft.get(key)}


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
                ): _dropdown(SENSOR_DEVICE_CLASSES),
                vol.Optional(
                    CONF_STATE_CLASS, description=_suggest(draft, CONF_STATE_CLASS)
                ): _dropdown(SENSOR_STATE_CLASSES),
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


def _validate_source(
    hass: HomeAssistant, user_input: dict[str, Any]
) -> tuple[dict[str, str], dict[str, str]]:
    """Form errors for the source fields, and the placeholders their texts need."""
    templates = user_input.get(CONF_ATTRIBUTE_TEMPLATES)
    if templates:
        if problem := attribute_template_error(templates):
            error, attribute = problem
            return {CONF_ATTRIBUTE_TEMPLATES: error}, {"attribute": attribute}
        for attribute, text in templates.items():
            try:
                Template(text, hass).ensure_valid()
            except TemplateError as err:
                return (
                    {CONF_ATTRIBUTE_TEMPLATES: "attribute_template_invalid"},
                    {"attribute": attribute, "error": str(err)},
                )
    return {}, {}


class VirtualDeviceSubentryFlow(ConfigSubentryFlow):
    """Create a virtual device or manage its entities."""

    def __init__(self) -> None:
        self._device_name = ""
        self._entities: list[dict[str, Any]] | None = None
        self._draft: dict[str, Any] = {}
        # True while a new entity is created (as opposed to edited): then values suggested by
        # the source entity fill the forms.
        self._adding = False
        # True when the source was already asked for, in the "add from source" path.
        self._source_done = False
        # What follows the "select attributes" step.
        self._proceed: Callable[[], Awaitable[SubentryFlowResult]] = self._show_basics

    @property
    def _working_copy(self) -> list[dict[str, Any]]:
        if self._entities is None:
            if self.source == SOURCE_RECONFIGURE:
                saved = self._get_reconfigure_subentry().data[CONF_ENTITIES]
                self._entities = deepcopy(list(saved))
            else:
                self._entities = []
        return self._entities

    def _merge(self, schema: vol.Schema, user_input: dict[str, Any]) -> None:
        """Take form input into the draft; fields that were cleared are removed."""
        for key in schema.schema:
            self._draft.pop(str(key), None)
        self._draft.update(user_input)

    def _commit_draft(self) -> None:
        draft = {k: v for k, v in self._draft.items() if v not in (None, "", [], {})}
        draft.setdefault(CONF_ID, uuid.uuid4().hex[:8])
        entities = self._working_copy
        for index, existing in enumerate(entities):
            if existing[CONF_ID] == draft[CONF_ID]:
                entities[index] = draft
                break
        else:
            entities.append(draft)
        self._draft = {}

    # ---- start: new device or existing device --------------------------------------------
    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        """Ask for the name of the new device."""
        if user_input is not None:
            self._device_name = user_input[CONF_DEVICE_NAME]
            return await self.async_step_init()
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({vol.Required(CONF_DEVICE_NAME): str})
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Manage the entities of an existing device."""
        return await self.async_step_init()

    # ---- menu -----------------------------------------------------------------------------
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        """Main menu."""
        menu = ["add_from_source", "add_entity"]
        if self._working_copy:
            menu += ["edit_entity", "remove_entity"]
        menu.append("save")
        return self.async_show_menu(step_id="init", menu_options=menu)

    async def async_step_save(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        """Store the working copy; the integration reloads afterwards."""
        data = {CONF_ENTITIES: self._working_copy}
        if self.source == SOURCE_RECONFIGURE:
            return self.async_update_and_abort(
                self._get_entry(), self._get_reconfigure_subentry(), data=data
            )
        return self.async_create_entry(title=self._device_name, data=data)

    # ---- remove / pick an entity ------------------------------------------------------------
    def _pick_options(self) -> list[SelectOptionDict]:
        return [
            SelectOptionDict(value=e[CONF_ID], label=f"{e[CONF_NAME]} ({e[CONF_PLATFORM]})")
            for e in self._working_copy
        ]

    async def async_step_remove_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
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
    ) -> SubentryFlowResult:
        """Choose the entity to edit, then continue with its (prefilled) forms."""
        if user_input is not None:
            chosen = next(e for e in self._working_copy if e[CONF_ID] == user_input[CONF_PICK])
            self._draft = deepcopy(chosen)
            self._adding = False
            self._source_done = False
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
    ) -> SubentryFlowResult:
        """Platform and name."""
        if user_input is None:
            self._draft = {}
            self._adding = True
            self._source_done = False
            return self._show_basics_form()
        platform = user_input[CONF_PLATFORM]
        if self._draft.get(CONF_PLATFORM, platform) != platform:
            # Platform changed while editing: keep only what all platforms share.
            self._draft = {k: v for k, v in self._draft.items() if k in _SHARED_KEYS}
        self._draft.pop(CONF_ICON, None)
        self._draft |= {CONF_PLATFORM: platform, CONF_NAME: user_input[CONF_NAME]}
        if icon := user_input.get(CONF_ICON):
            self._draft[CONF_ICON] = icon
        if platform == Platform.BUTTON:
            for key in _SOURCE_KEYS:
                self._draft.pop(key, None)
            return await self.async_step_entity_details()
        if self._source_done:
            return await self._next_after_source()
        return await self.async_step_entity_source()

    async def async_step_add_from_source(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Start with the source; type and name are then suggested from it."""
        if user_input is None:
            self._draft = {}
            self._adding = True
            self._source_done = True
            return self._show_source_form("add_from_source")
        errors, placeholders = _validate_source(self.hass, user_input)
        if errors:
            self._draft |= user_input
            return self._show_source_form("add_from_source", errors, placeholders)
        self._take_source(user_input)
        suggestions = defaults_from_source(self.hass.states.get(user_input[CONF_SOURCE_ENTITY]))
        self._draft |= {k: v for k, v in suggestions.items() if k in (CONF_NAME, CONF_PLATFORM)}
        return await self._after_source_form(self._show_basics)

    def _show_basics_form(self) -> SubentryFlowResult:
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
                vol.Optional(
                    CONF_ICON, description=_suggest(self._draft, CONF_ICON)
                ): IconSelector(),
            }
        )
        return self.async_show_form(step_id="add_entity", data_schema=schema)

    async def async_step_entity_source(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Source entity, source attribute, value template and copied attributes."""
        if user_input is not None:
            errors, placeholders = _validate_source(self.hass, user_input)
            if errors:
                self._draft |= user_input
                return self._show_source_form("entity_source", errors, placeholders)
            self._take_source(user_input)
            return await self._after_source_form(self._next_after_source)
        return self._show_source_form("entity_source")

    async def _after_source_form(
        self, proceed: Callable[[], Awaitable[SubentryFlowResult]]
    ) -> SubentryFlowResult:
        """Ask for the attributes to copy if they are selected, then go on."""
        if self._draft.get(CONF_COPY_ATTRIBUTES) != COPY_SELECTED:
            self._draft.pop(CONF_ATTRIBUTE_NAMES, None)
            return await proceed()
        self._proceed = proceed
        return await self.async_step_select_attributes()

    async def async_step_select_attributes(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Choose the attributes to copy, offering the ones the source has."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_ATTRIBUTE_NAMES]:
                self._draft[CONF_ATTRIBUTE_NAMES] = user_input[CONF_ATTRIBUTE_NAMES]
                return await self._proceed()
            errors[CONF_ATTRIBUTE_NAMES] = "attribute_names_required"
        source = self.hass.states.get(self._draft.get(CONF_SOURCE_ENTITY, ""))
        offered = sorted(set(source.attributes) - RESERVED_ATTRIBUTES) if source else []
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_ATTRIBUTE_NAMES, description=_suggest(self._draft, CONF_ATTRIBUTE_NAMES)
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=offered,
                        multiple=True,
                        custom_value=True,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
        return self.async_show_form(step_id="select_attributes", data_schema=schema, errors=errors)

    async def _show_basics(self) -> SubentryFlowResult:
        return self._show_basics_form()

    def _show_source_form(
        self,
        step_id: str,
        errors: dict[str, str] | None = None,
        placeholders: dict[str, str] | None = None,
    ) -> SubentryFlowResult:
        return self.async_show_form(
            step_id=step_id,
            data_schema=self._source_schema(),
            errors=errors,
            description_placeholders=placeholders,
        )

    def _take_source(self, user_input: dict[str, Any]) -> None:
        """Take the source form into the draft; names stay only while attributes are selected."""
        names = self._draft.get(CONF_ATTRIBUTE_NAMES)
        for key in _SOURCE_KEYS:
            self._draft.pop(key, None)
        self._draft |= user_input
        if user_input.get(CONF_COPY_ATTRIBUTES) == COPY_SELECTED and names:
            self._draft[CONF_ATTRIBUTE_NAMES] = names  # shown again as the current choice

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
                vol.Optional(
                    CONF_COPY_ATTRIBUTES, description=_suggest(self._draft, CONF_COPY_ATTRIBUTES)
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=list(COPY_MODES),
                        mode=SelectSelectorMode.DROPDOWN,
                        translation_key="copy_attributes",
                    )
                ),
                vol.Optional(
                    CONF_ATTRIBUTE_TEMPLATES,
                    description=_suggest(self._draft, CONF_ATTRIBUTE_TEMPLATES),
                ): ObjectSelector(),
            }
        )

    async def _next_after_source(self) -> SubentryFlowResult:
        if _details_schema(self._draft[CONF_PLATFORM], self._draft) is not None:
            return await self.async_step_entity_details()
        self._commit_draft()
        return await self.async_step_init()

    async def async_step_entity_details(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Platform specific settings, such as the actions forwarding commands."""
        platform = self._draft[CONF_PLATFORM]
        if user_input is None and self._adding:
            self._suggest_from_source(platform)
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

    def _suggest_from_source(self, platform: str) -> None:
        """Fill details the user has not set yet: settings and forwarding actions of the source."""
        schema = _details_schema(platform, self._draft)
        assert schema is not None
        wanted = {str(key) for key in schema.schema}
        source = self.hass.states.get(self._draft.get(CONF_SOURCE_ENTITY, ""))
        for key, value in (defaults_from_source(source) | forwarding_actions(source)).items():
            if key in wanted:
                self._draft.setdefault(key, value)
