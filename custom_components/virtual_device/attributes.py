"""Pure logic: which attributes of the source entity are copied to a virtual entity."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .const import (
    ATTR_FORWARDS_COMMANDS,
    ATTR_SOURCE_ATTRIBUTE,
    ATTR_SOURCE_ENTITY,
    CONF_ATTRIBUTE_NAMES,
    CONF_COPY_ATTRIBUTES,
    COPY_ALL,
    COPY_SELECTED,
)

# Attributes Home Assistant derives from the virtual entity itself, and the ones marking where it
# is wired to; copying them would clash with its own name, icon, unit, classes and marking.
RESERVED_ATTRIBUTES = frozenset(
    {
        "friendly_name",
        "icon",
        "entity_picture",
        "unit_of_measurement",
        "device_class",
        "state_class",
        "supported_features",
        "assumed_state",
        "options",
        "min",
        "max",
        "step",
        "mode",
        ATTR_SOURCE_ENTITY,
        ATTR_SOURCE_ATTRIBUTE,
        ATTR_FORWARDS_COMMANDS,
    }
)


def copied_attributes(
    config: Mapping[str, Any], source_attributes: Mapping[str, Any] | None
) -> dict[str, Any]:
    """The attributes of the source that the entity definition asks to copy."""
    if source_attributes is None:
        return {}
    mode = config.get(CONF_COPY_ATTRIBUTES)
    if mode == COPY_ALL:
        names = list(source_attributes)
    elif mode == COPY_SELECTED:
        names = [n for n in config.get(CONF_ATTRIBUTE_NAMES, []) if n in source_attributes]
    else:
        return {}
    return {n: source_attributes[n] for n in names if n not in RESERVED_ATTRIBUTES}


def attribute_template_error(templates: Any) -> tuple[str, str] | None:
    """The first problem of an attribute templates input as (error key, attribute name)."""
    if not isinstance(templates, Mapping):
        return "attribute_templates_invalid", ""
    for name, template in templates.items():
        if not isinstance(name, str) or not name.strip():
            return "attribute_templates_invalid", str(name)
        if not isinstance(template, str) or not template.strip():
            return "attribute_templates_invalid", name
        if name in RESERVED_ATTRIBUTES:
            return "attribute_name_reserved", name
    return None
