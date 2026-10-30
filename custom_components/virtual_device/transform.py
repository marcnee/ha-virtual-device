"""Turning a raw source value into the value of a virtual entity."""

from __future__ import annotations

import logging
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
