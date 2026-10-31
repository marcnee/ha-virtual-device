"""A preview of the templates of an entity, rendered with the current state of its source."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import TemplateError

from .const import (
    CONF_ATTRIBUTE_TEMPLATES,
    CONF_EXTRA_SOURCES,
    CONF_SOURCE_ATTRIBUTE,
    CONF_SOURCE_ENTITY,
    CONF_VALUE_TEMPLATE,
)
from .transform import AttributeTransformer, ValueTransformer, raw_value

NOTHING = "\u2013"  # shown where there is no value
_ERROR = "⚠ "
# The texts of the preview are made here, so that lines that do not apply can be left out.
_TITLE = "**Preview** with the current state of the source:"
_VALUE = "Value of the source: "
_RESULT = "Result of the value template: "
_ATTRIBUTES = "Attribute templates: "
_MAX_LENGTH = 80


def _show(value: Any) -> str:
    """A value as a short piece of code that cannot break the text around it."""
    if value is None:
        return NOTHING
    text = " ".join(str(value).replace("`", "'").split())
    if len(text) > _MAX_LENGTH:
        text = text[: _MAX_LENGTH - 1] + "…"
    return f"`{text}`"


def _show_error(error: TemplateError) -> str:
    return _ERROR + " ".join(str(error).split())


def _usable(templates: Any) -> dict[str, str]:
    """The attribute templates that are well-formed; the input may not have passed the checks."""
    if not isinstance(templates, Mapping):
        return {}
    return {
        name: text
        for name, text in templates.items()
        if isinstance(name, str) and name.strip() and isinstance(text, str) and text.strip()
    }


def build_preview(hass: HomeAssistant, config: Mapping[str, Any], state: State | None) -> str:
    """The text for a form: the value of the source and what the templates make of it.

    Empty as long as no source is chosen. Only the templates that are set get a line.
    """
    if not config.get(CONF_SOURCE_ENTITY):
        return ""
    extras = config.get(CONF_EXTRA_SOURCES, [])
    lines = []
    raw = None if state is None else raw_value(state, config.get(CONF_SOURCE_ATTRIBUTE))
    lines.append(f"{_VALUE}{_show(raw)}")
    if state is not None:
        if template := config.get(CONF_VALUE_TEMPLATE):
            try:
                result = _show(ValueTransformer(hass, template, "", extras).render(raw, state))
            except TemplateError as err:
                result = _show_error(err)
            lines.append(f"{_RESULT}{result}")
        if templates := _usable(config.get(CONF_ATTRIBUTE_TEMPLATES)):
            rendered = AttributeTransformer(hass, templates, "", extras).render(raw, state)
            results = ", ".join(
                f"`{name}`: " + (_show_error(r) if isinstance(r, TemplateError) else _show(r))
                for name, r in rendered.items()
            )
            lines.append(f"{_ATTRIBUTES}{results}")
    return _TITLE + "".join(f"\n- {line}" for line in lines)
