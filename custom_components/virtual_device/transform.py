"""Turning a raw source value into the value of a virtual entity."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.template import Template

_LOGGER = logging.getLogger(__name__)

# Rendered template results that mean "no value".
_NO_VALUE = frozenset({"", "none", "unknown", "unavailable"})


def raw_value(state: State, attribute: str | None) -> Any | None:
    """The attribute or the state of the source; None if it has no value."""
    if attribute:
        return state.attributes.get(attribute)
    return None if state.state == STATE_UNKNOWN else state.state


def _variables(raw: Any, state: State) -> dict[str, Any]:
    """What the templates can use."""
    return {"value": raw, "state": state, "attributes": state.attributes}


class ValueTransformer:
    """Applies an optional Jinja template to a source value.

    The template sees `value` (state or attribute), `state` and `attributes`.
    """

    def __init__(self, hass: HomeAssistant, template: str | None, name: str) -> None:
        self._template = Template(template, hass) if template else None
        self._name = name

    def render(self, raw: Any, state: State) -> Any | None:
        """The transformed value, or None if there is no value. A failing template raises."""
        if raw is None:
            return None
        if self._template is None:
            return raw
        result = self._template.async_render(_variables(raw, state), parse_result=False)
        return None if result.strip().lower() in _NO_VALUE else result

    def __call__(self, raw: Any, state: State) -> Any | None:
        """Like `render`, but a failing template is logged and gives no value."""
        try:
            return self.render(raw, state)
        except TemplateError as err:
            _LOGGER.warning("Template of '%s' failed for value %r: %s", self._name, raw, err)
            return None


class AttributeTransformer:
    """Computes extra attributes from templates; same variables as the value template."""

    def __init__(self, hass: HomeAssistant, templates: Mapping[str, str], name: str) -> None:
        self._templates = {attr: Template(text, hass) for attr, text in templates.items()}
        self._name = name

    def render(self, raw: Any, state: State) -> dict[str, Any]:
        """The result of every template; for a failing one the TemplateError itself."""
        variables = _variables(raw, state)
        rendered: dict[str, Any] = {}
        for attr, template in self._templates.items():
            try:
                rendered[attr] = template.async_render(variables)
            except TemplateError as err:
                rendered[attr] = err
        return rendered

    def __call__(self, raw: Any, state: State) -> dict[str, Any]:
        """Attributes that rendered to a value; failing or empty ones are left out."""
        attributes: dict[str, Any] = {}
        for attr, result in self.render(raw, state).items():
            if isinstance(result, TemplateError):
                _LOGGER.warning(
                    "Attribute template '%s' of '%s' failed: %s", attr, self._name, result
                )
            elif result is not None:
                attributes[attr] = result
        return attributes


# Values that mean "on". Everything else means "off"; use a template for other conventions.
_TRUE_VALUES = frozenset({"on", "true", "1", "yes"})


def to_bool(value: Any) -> bool:
    """Interpret a (transformed) value as on/off."""
    return str(value).strip().lower() in _TRUE_VALUES
