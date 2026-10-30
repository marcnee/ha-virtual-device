"""A preview of the templates of an entity, rendered with the current state of its source."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import TemplateError

from .const import CONF_ATTRIBUTE_TEMPLATES, CONF_SOURCE_ATTRIBUTE, CONF_VALUE_TEMPLATE
from .transform import AttributeTransformer, ValueTransformer, raw_value

NOTHING = "\u2013"  # shown where there is no value
_ERROR = "⚠ "
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


def build_preview(
    hass: HomeAssistant, config: Mapping[str, Any], state: State | None
) -> dict[str, str]:
    """Texts for the form: the value of the source and what the templates make of it."""
    preview = {"source_value": NOTHING, "value_result": NOTHING, "attribute_results": NOTHING}
    if state is None:
        return preview
    raw = raw_value(state, config.get(CONF_SOURCE_ATTRIBUTE))
    preview["source_value"] = _show(raw)
    if template := config.get(CONF_VALUE_TEMPLATE):
        try:
            preview["value_result"] = _show(ValueTransformer(hass, template, "").render(raw, state))
        except TemplateError as err:
            preview["value_result"] = _show_error(err)
    if templates := config.get(CONF_ATTRIBUTE_TEMPLATES):
        rendered = AttributeTransformer(hass, templates, "").render(raw, state)
        preview["attribute_results"] = ", ".join(
            f"`{name}`: " + (_show_error(r) if isinstance(r, TemplateError) else _show(r))
            for name, r in rendered.items()
        )
    return preview
