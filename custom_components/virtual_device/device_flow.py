"""Subentry flow: create a virtual device, or add, edit and remove its entities.

Changes are collected in a working copy and only stored when "save" is chosen.
"""

from __future__ import annotations

import uuid
from copy import deepcopy
from enum import Enum, auto
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import SOURCE_RECONFIGURE, ConfigSubentryFlow, SubentryFlowResult
from homeassistant.const import Platform
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .attributes import RESERVED_ATTRIBUTES
from .const import (
    CONF_ATTRIBUTE_NAMES,
    CONF_ATTRIBUTE_TEMPLATES,
    CONF_COPY_ATTRIBUTES,
    CONF_DEVICE_NAME,
    CONF_ENTITIES,
    CONF_ICON,
    CONF_ID,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_NAME,
    CONF_PICK,
    CONF_PLATFORM,
    CONF_SOURCE_ATTRIBUTE,
    CONF_SOURCE_ENTITY,
    CONF_TEST_TEMPLATE,
    CONF_VALUE_TEMPLATE,
    COPY_SELECTED,
)
from .flow_forms import (
    attributes_schema,
    basics_schema,
    details_schema,
    device_schema,
    source_schema,
)
from .flow_validation import validate_details, validate_source
from .forwarding import forwarding_actions
from .source_defaults import defaults_from_source
from .template_preview import build_preview

# Fields kept when the platform of an entity is changed while editing.
_SOURCE_KEYS = (
    CONF_SOURCE_ENTITY,
    CONF_SOURCE_ATTRIBUTE,
    CONF_VALUE_TEMPLATE,
    CONF_COPY_ATTRIBUTES,
    CONF_ATTRIBUTE_NAMES,
    CONF_ATTRIBUTE_TEMPLATES,
)
# Optional text properties of the device, besides its name.
_DEVICE_KEYS = (CONF_MANUFACTURER, CONF_MODEL)
_SHARED_KEYS = {CONF_ID, CONF_ICON, *_SOURCE_KEYS}


class _Mode(Enum):
    """How the entity in the draft is being created or changed."""

    ADD = auto()  # type and name first, then the source
    ADD_FROM_SOURCE = auto()  # the source first; type and name are suggested from it
    EDIT = auto()  # type and name first, then the source; all forms are prefilled


class VirtualDeviceSubentryFlow(ConfigSubentryFlow):
    """Create a virtual device or manage its entities."""

    def __init__(self) -> None:
        # Name, manufacturer and model of the device; loaded when first needed.
        self._device: dict[str, str] | None = None
        self._entities: list[dict[str, Any]] | None = None
        self._draft: dict[str, Any] = {}
        self._mode = _Mode.ADD

    @property
    def _adding(self) -> bool:
        """A new entity is created (not edited): values suggested by the source fill the forms."""
        return self._mode is not _Mode.EDIT

    @property
    def _source_first(self) -> bool:
        """The source was asked for before type and name."""
        return self._mode is _Mode.ADD_FROM_SOURCE

    @property
    def _device_settings(self) -> dict[str, str]:
        if self._device is None:
            if self.source == SOURCE_RECONFIGURE:
                subentry = self._get_reconfigure_subentry()
                saved = {k: subentry.data[k] for k in _DEVICE_KEYS if k in subentry.data}
                self._device = {CONF_DEVICE_NAME: subentry.title} | saved
            else:
                self._device = {}
        return self._device

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
        """Ask for the name, manufacturer and model of the new device."""
        if user_input is not None:
            self._take_device_settings(user_input)
            return await self.async_step_init()
        return self._show_device_form("user")

    async def async_step_device_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Change name, manufacturer and model of an existing device."""
        if user_input is not None:
            self._take_device_settings(user_input)
            return await self.async_step_init()
        return self._show_device_form("device_settings")

    def _show_device_form(self, step_id: str) -> SubentryFlowResult:
        current = self._device_settings
        schema = device_schema(current)
        return self.async_show_form(step_id=step_id, data_schema=schema)

    def _take_device_settings(self, user_input: dict[str, Any]) -> None:
        """Cleared optional fields are removed."""
        self._device = {k: v.strip() for k, v in user_input.items() if v and v.strip()}

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
        if self.source == SOURCE_RECONFIGURE:
            menu.append("device_settings")
        menu.append("save")
        return self.async_show_menu(step_id="init", menu_options=menu)

    async def async_step_save(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        """Store the working copy; the integration reloads afterwards."""
        device = self._device_settings
        data = {CONF_ENTITIES: self._working_copy} | {
            k: device[k] for k in _DEVICE_KEYS if k in device
        }
        if self.source == SOURCE_RECONFIGURE:
            return self.async_update_and_abort(
                self._get_entry(),
                self._get_reconfigure_subentry(),
                title=device[CONF_DEVICE_NAME],
                data=data,
            )
        return self.async_create_entry(title=device[CONF_DEVICE_NAME], data=data)

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
            self._mode = _Mode.EDIT
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
            self._mode = _Mode.ADD
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
        if self._source_first:
            return await self.async_step_entity_details()
        return await self.async_step_entity_source()

    async def async_step_add_from_source(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Start with the source; type and name are then suggested from it."""
        if user_input is None:
            self._draft = {}
            self._mode = _Mode.ADD_FROM_SOURCE
            return self._show_source_form("add_from_source")
        if (again := self._take_source_input("add_from_source", user_input)) is not None:
            return again
        suggestions = defaults_from_source(self.hass.states.get(user_input[CONF_SOURCE_ENTITY]))
        self._draft |= {k: v for k, v in suggestions.items() if k in (CONF_NAME, CONF_PLATFORM)}
        return await self._after_source_form()

    def _show_basics_form(self) -> SubentryFlowResult:
        return self.async_show_form(step_id="add_entity", data_schema=basics_schema(self._draft))

    async def async_step_entity_source(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Source entity, source attribute, value template and copied attributes."""
        if user_input is not None:
            if (again := self._take_source_input("entity_source", user_input)) is not None:
                return again
            return await self._after_source_form()
        return self._show_source_form("entity_source")

    async def _after_source_form(self) -> SubentryFlowResult:
        """Ask for the attributes to copy if they are selected, then go on."""
        if self._draft.get(CONF_COPY_ATTRIBUTES) != COPY_SELECTED:
            self._draft.pop(CONF_ATTRIBUTE_NAMES, None)
            return await self._after_attributes()
        return await self.async_step_select_attributes()

    async def _after_attributes(self) -> SubentryFlowResult:
        """With the source first, type and name follow; otherwise the details."""
        if self._source_first:
            return self._show_basics_form()
        return await self.async_step_entity_details()

    async def async_step_select_attributes(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Choose the attributes to copy, offering the ones the source has."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_ATTRIBUTE_NAMES]:
                self._draft[CONF_ATTRIBUTE_NAMES] = user_input[CONF_ATTRIBUTE_NAMES]
                return await self._after_attributes()
            errors[CONF_ATTRIBUTE_NAMES] = "attribute_names_required"
        source = self.hass.states.get(self._draft.get(CONF_SOURCE_ENTITY, ""))
        offered = sorted(set(source.attributes) - RESERVED_ATTRIBUTES) if source else []
        schema = attributes_schema(self._draft, offered)
        return self.async_show_form(step_id="select_attributes", data_schema=schema, errors=errors)

    def _take_source_input(
        self, step_id: str, user_input: dict[str, Any]
    ) -> SubentryFlowResult | None:
        """Take the source form into the draft.

        Returns the form to show again if the input has errors or if the user asked to test the
        templates; None if the flow goes on.
        """
        user_input = dict(user_input)
        test = user_input.pop(CONF_TEST_TEMPLATE, False)
        errors, placeholders = validate_source(self.hass, user_input)
        if errors:
            self._draft |= user_input
            return self._show_source_form(step_id, errors, placeholders)
        self._take_source(user_input)
        return self._show_source_form(step_id) if test else None

    def _show_source_form(
        self,
        step_id: str,
        errors: dict[str, str] | None = None,
        placeholders: dict[str, str] | None = None,
    ) -> SubentryFlowResult:
        """The source form, with what the templates make of the current state of the source."""
        source = self.hass.states.get(self._draft.get(CONF_SOURCE_ENTITY, ""))
        return self.async_show_form(
            step_id=step_id,
            data_schema=source_schema(self._draft),
            errors=errors,
            description_placeholders={"preview": build_preview(self.hass, self._draft, source)}
            | (placeholders or {}),
        )

    def _take_source(self, user_input: dict[str, Any]) -> None:
        """Take the source form into the draft; names stay only while attributes are selected."""
        names = self._draft.get(CONF_ATTRIBUTE_NAMES)
        for key in _SOURCE_KEYS:
            self._draft.pop(key, None)
        self._draft |= user_input
        if user_input.get(CONF_COPY_ATTRIBUTES) == COPY_SELECTED and names:
            self._draft[CONF_ATTRIBUTE_NAMES] = names  # shown again as the current choice

    async def async_step_entity_details(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Platform specific settings, such as the actions forwarding commands."""
        platform = self._draft[CONF_PLATFORM]
        if user_input is None and self._adding:
            self._suggest_from_source(platform)
        schema = details_schema(platform, self._draft)
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = validate_details(platform, user_input)
            if not errors:
                self._merge(schema, user_input)
                self._commit_draft()
                return await self.async_step_init()
            self._draft |= user_input
            schema = details_schema(platform, self._draft)
        return self.async_show_form(step_id="entity_details", data_schema=schema, errors=errors)

    def _suggest_from_source(self, platform: str) -> None:
        """Fill details the user has not set yet: settings and forwarding actions of the source."""
        schema = details_schema(platform, self._draft)
        wanted = {str(key) for key in schema.schema}
        source = self.hass.states.get(self._draft.get(CONF_SOURCE_ENTITY, ""))
        for key, value in (
            defaults_from_source(source, platform) | forwarding_actions(source)
        ).items():
            if key in wanted:
                self._draft.setdefault(key, value)
