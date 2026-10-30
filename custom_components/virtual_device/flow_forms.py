"""The forms of the flow that creates and edits virtual devices (schemas only, no logic)."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.const import Platform
from homeassistant.helpers.selector import (
    ActionSelector,
    BooleanSelector,
    EntitySelector,
    IconSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    ObjectSelector,
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
    CONF_ATTRIBUTE_NAMES,
    CONF_ATTRIBUTE_TEMPLATES,
    CONF_COPY_ATTRIBUTES,
    CONF_DEVICE_CLASS,
    CONF_DEVICE_NAME,
    CONF_ICON,
    CONF_MANUFACTURER,
    CONF_MAX,
    CONF_MIN,
    CONF_MODEL,
    CONF_NAME,
    CONF_OPTIONS,
    CONF_PLATFORM,
    CONF_SOURCE_ATTRIBUTE,
    CONF_SOURCE_ENTITY,
    CONF_STATE_CLASS,
    CONF_STEP,
    CONF_TEST_TEMPLATE,
    CONF_UNIT,
    CONF_VALUE_TEMPLATE,
    COPY_MODES,
    PLATFORMS,
)
from .device_classes import (
    BINARY_SENSOR_DEVICE_CLASSES,
    SENSOR_DEVICE_CLASSES,
    SENSOR_STATE_CLASSES,
)


def suggest(draft: dict[str, Any], key: str) -> dict[str, Any]:
    """Prefill a form field from the entity being edited."""
    return {"suggested_value": draft.get(key)}


def dropdown(options: list[str]) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN, sort=True)
    )


def action_field(draft: dict[str, Any], key: str) -> dict[Any, Any]:
    return {vol.Optional(key, description=suggest(draft, key)): ActionSelector()}


def details_schema(platform: str, draft: dict[str, Any]) -> vol.Schema:
    """The fields that are specific to the type of the entity."""
    fields: dict[Any, Any]
    match platform:
        case Platform.SENSOR:
            fields = {
                vol.Optional(CONF_UNIT, description=suggest(draft, CONF_UNIT)): TextSelector(),
                vol.Optional(
                    CONF_DEVICE_CLASS, description=suggest(draft, CONF_DEVICE_CLASS)
                ): dropdown(SENSOR_DEVICE_CLASSES),
                vol.Optional(
                    CONF_STATE_CLASS, description=suggest(draft, CONF_STATE_CLASS)
                ): dropdown(SENSOR_STATE_CLASSES),
            }
        case Platform.BINARY_SENSOR:
            fields = {
                vol.Optional(
                    CONF_DEVICE_CLASS, description=suggest(draft, CONF_DEVICE_CLASS)
                ): dropdown(BINARY_SENSOR_DEVICE_CLASSES)
            }
        case Platform.SWITCH:
            fields = action_field(draft, CONF_ACTION_ON) | action_field(draft, CONF_ACTION_OFF)
        case Platform.NUMBER:
            number = NumberSelector(NumberSelectorConfig(mode=NumberSelectorMode.BOX, step="any"))
            fields = {
                vol.Required(CONF_MIN, default=draft.get(CONF_MIN, 0)): number,
                vol.Required(CONF_MAX, default=draft.get(CONF_MAX, 100)): number,
                vol.Required(CONF_STEP, default=draft.get(CONF_STEP, 1)): number,
                vol.Optional(CONF_UNIT, description=suggest(draft, CONF_UNIT)): TextSelector(),
            } | action_field(draft, CONF_ACTION_SET)
        case Platform.SELECT:
            fields = {
                vol.Optional(CONF_OPTIONS, description=suggest(draft, CONF_OPTIONS)): TextSelector(
                    TextSelectorConfig(multiple=True)
                )
            } | action_field(draft, CONF_ACTION_SELECT)
        case Platform.BUTTON:
            fields = action_field(draft, CONF_ACTION_PRESS)
        case _:
            raise ValueError(f"Unknown platform {platform}")
    return vol.Schema(fields)


def basics_schema(draft: dict[str, Any]) -> vol.Schema:
    """Type, name and icon of an entity."""
    return vol.Schema(
        {
            vol.Required(
                CONF_PLATFORM, default=draft.get(CONF_PLATFORM, Platform.SENSOR)
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[str(p) for p in PLATFORMS],
                    mode=SelectSelectorMode.DROPDOWN,
                    translation_key="platform",
                )
            ),
            vol.Required(CONF_NAME, default=draft.get(CONF_NAME, "")): TextSelector(),
            vol.Optional(CONF_ICON, description=suggest(draft, CONF_ICON)): IconSelector(),
        }
    )


def source_schema(draft: dict[str, Any]) -> vol.Schema:
    """Source entity or attribute, value template and the attributes to copy."""
    return vol.Schema(
        {
            vol.Required(
                CONF_SOURCE_ENTITY, description=suggest(draft, CONF_SOURCE_ENTITY)
            ): EntitySelector(),
            vol.Optional(
                CONF_SOURCE_ATTRIBUTE, description=suggest(draft, CONF_SOURCE_ATTRIBUTE)
            ): TextSelector(),
            vol.Optional(
                CONF_VALUE_TEMPLATE, description=suggest(draft, CONF_VALUE_TEMPLATE)
            ): TemplateSelector(),
            vol.Optional(
                CONF_COPY_ATTRIBUTES, description=suggest(draft, CONF_COPY_ATTRIBUTES)
            ): SelectSelector(
                SelectSelectorConfig(
                    options=list(COPY_MODES),
                    mode=SelectSelectorMode.DROPDOWN,
                    translation_key="copy_attributes",
                )
            ),
            vol.Optional(
                CONF_ATTRIBUTE_TEMPLATES, description=suggest(draft, CONF_ATTRIBUTE_TEMPLATES)
            ): ObjectSelector(),
            vol.Optional(CONF_TEST_TEMPLATE): BooleanSelector(),
        }
    )


def attributes_schema(draft: dict[str, Any], offered: list[str]) -> vol.Schema:
    """The attributes of the source to copy; others can be typed in."""
    return vol.Schema(
        {
            vol.Required(
                CONF_ATTRIBUTE_NAMES, description=suggest(draft, CONF_ATTRIBUTE_NAMES)
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


def device_schema(current: dict[str, str]) -> vol.Schema:
    """Name, manufacturer and model of a virtual device."""
    return vol.Schema(
        {
            vol.Required(CONF_DEVICE_NAME, description=suggest(current, CONF_DEVICE_NAME)): (
                TextSelector()
            ),
            vol.Optional(CONF_MANUFACTURER, description=suggest(current, CONF_MANUFACTURER)): (
                TextSelector()
            ),
            vol.Optional(CONF_MODEL, description=suggest(current, CONF_MODEL)): TextSelector(),
        }
    )
