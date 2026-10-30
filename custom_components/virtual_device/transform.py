"""Turning a raw source value into the value of a virtual entity."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.template import Template

_LOGGER = logging.getLogger(__name__)

# Rendered template results that mean "no value".
_NO_VALUE = frozenset({"", "none", "unknown", "unavailable"})


class ValueTransformer:
    """Applies an optional Jinja template to a source value.

    The template sees `value` (state or attribute), `state` and `attributes`.
    """

    def __init__(self, hass: HomeAssistant, template: str | None, name: str) -> None:
        self._template = Template(template, hass) if template else None
        self._name = name

    def __call__(self, raw: Any, state: State) -> Any | None:
        """Return the transformed value, or None if there is no value."""
        if raw is None:
            return None
        if self._template is None:
            return raw
        variables = {"value": raw, "state": state, "attributes": state.attributes}
        try:
            result = self._template.async_render(variables, parse_result=False)
        except TemplateError as err:
            _LOGGER.warning("Template of '%s' failed for value %r: %s", self._name, raw, err)
            return None
        return None if result.strip().lower() in _NO_VALUE else result


class AttributeTransformer:
    """Computes extra attributes from templates; same variables as the value template."""

    def __init__(self, hass: HomeAssistant, templates: Mapping[str, str], name: str) -> None:
        self._templates = {attr: Template(text, hass) for attr, text in templates.items()}
        self._name = name

    def __call__(self, raw: Any, state: State) -> dict[str, Any]:
        """Attributes that rendered to a value; failing or empty ones are left out."""
        variables = {"value": raw, "state": state, "attributes": state.attributes}
        attributes: dict[str, Any] = {}
        for attr, template in self._templates.items():
            try:
                result = template.async_render(variables)
            except TemplateError as err:
                _LOGGER.warning("Attribute template '%s' of '%s' failed: %s", attr, self._name, err)
                continue
            if result is not None:
                attributes[attr] = result
        return attributes


# Values that mean "on". Everything else means "off"; use a template for other conventions.
_TRUE_VALUES = frozenset({"on", "true", "1", "yes"})


def to_bool(value: Any) -> bool:
    """Interpret a (transformed) value as on/off."""
    return str(value).strip().lower() in _TRUE_VALUES
