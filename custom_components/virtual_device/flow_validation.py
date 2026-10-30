"""Checks of what the user entered in the flow forms."""

from __future__ import annotations

from typing import Any

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.template import Template

from .attributes import attribute_template_error
from .const import CONF_ATTRIBUTE_TEMPLATES, CONF_MAX, CONF_MIN, CONF_OPTIONS


def validate_details(platform: str, user_input: dict[str, Any]) -> dict[str, str]:
    """Form errors for the platform specific fields."""
    errors: dict[str, str] = {}
    if platform == Platform.NUMBER and user_input[CONF_MIN] >= user_input[CONF_MAX]:
        errors[CONF_MAX] = "min_greater_max"
    if platform == Platform.SELECT and not user_input.get(CONF_OPTIONS):
        errors[CONF_OPTIONS] = "options_required"
    return errors


def validate_source(
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
