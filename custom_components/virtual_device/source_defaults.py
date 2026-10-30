"""Suggested settings for a virtual entity, derived from its source entity."""

from __future__ import annotations

from typing import Any

from homeassistant.const import Platform
from homeassistant.core import State

from .const import (
    CONF_DEVICE_CLASS,
    CONF_MAX,
    CONF_MIN,
    CONF_NAME,
    CONF_OPTIONS,
    CONF_PLATFORM,
    CONF_STATE_CLASS,
    CONF_STEP,
    CONF_UNIT,
)
from .device_classes import SENSOR_DEVICE_CLASSES, SENSOR_STATE_CLASSES

_PLATFORM_BY_DOMAIN = {
    "number": Platform.NUMBER,
    "input_number": Platform.NUMBER,
    "switch": Platform.SWITCH,
    "input_boolean": Platform.SWITCH,
    "select": Platform.SELECT,
    "input_select": Platform.SELECT,
    "binary_sensor": Platform.BINARY_SENSOR,
}

# Attribute of the source -> key of the virtual entity, with an optional allow-list.
_ATTRIBUTES: tuple[tuple[str, str, list[str] | None], ...] = (
    ("unit_of_measurement", CONF_UNIT, None),
    ("device_class", CONF_DEVICE_CLASS, SENSOR_DEVICE_CLASSES),
    ("state_class", CONF_STATE_CLASS, SENSOR_STATE_CLASSES),
    ("min", CONF_MIN, None),
    ("max", CONF_MAX, None),
    ("step", CONF_STEP, None),
    ("options", CONF_OPTIONS, None),
)


def defaults_from_source(state: State | None) -> dict[str, Any]:
    """Name, type, unit, classes, range and options suggested by the source."""
    if state is None:
        return {}
    defaults: dict[str, Any] = {
        CONF_NAME: state.name,
        CONF_PLATFORM: str(_PLATFORM_BY_DOMAIN.get(state.domain, Platform.SENSOR)),
    }
    for attribute, key, allowed in _ATTRIBUTES:
        value = state.attributes.get(attribute)
        if value is not None and (allowed is None or value in allowed):
            defaults[key] = value
    return defaults
