"""The source forms take attribute templates as YAML."""

from typing import Any
from unittest.mock import ANY

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.virtual_device.const import (
    CONF_ATTRIBUTE_TEMPLATES,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
)

from .conftest import SetupDevice
from .helpers import choose, reconfigure, save, saved_entities, source_form, submit, suggested

SOURCE = "sensor.heatpump_status"
BASICS = {CONF_PLATFORM: "binary_sensor", CONF_NAME: "Running"}
TEMPLATES = {"fehlercode": "{{ attributes.error_code | int }}", "text": "{{ value }}"}


def stored(**extra: Any) -> dict[str, Any]:
    return {CONF_ID: ANY, CONF_SOURCE_ENTITY: SOURCE} | BASICS | extra


async def test_attribute_templates_are_stored(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([])
    result = await source_form(hass, entry, BASICS)

    result = await submit(
        hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE, CONF_ATTRIBUTE_TEMPLATES: TEMPLATES}
    )
    await save(hass, result)

    assert saved_entities(entry) == [stored(**{CONF_ATTRIBUTE_TEMPLATES: TEMPLATES})]


async def test_empty_attribute_templates_are_not_stored(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([])
    result = await source_form(hass, entry, BASICS)

    result = await submit(
        hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE, CONF_ATTRIBUTE_TEMPLATES: {}}
    )
    await save(hass, result)

    assert saved_entities(entry) == [stored()]


async def submit_templates(
    hass: HomeAssistant, setup_device: SetupDevice, templates: Any
) -> dict[str, Any]:
    entry = await setup_device([])
    result = await source_form(hass, entry, BASICS)
    return await submit(
        hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE, CONF_ATTRIBUTE_TEMPLATES: templates}
    )


async def test_a_template_with_a_syntax_error_is_rejected(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    result = await submit_templates(hass, setup_device, {"ok": "{{ 1 }}", "broken": "{{ 1 +"})

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "entity_source"
    assert result["errors"] == {CONF_ATTRIBUTE_TEMPLATES: "attribute_template_invalid"}
    assert result["description_placeholders"]["attribute"] == "broken"
    assert result["description_placeholders"]["error"]
    assert suggested(result)[CONF_ATTRIBUTE_TEMPLATES] == {"ok": "{{ 1 }}", "broken": "{{ 1 +"}


async def test_a_reserved_attribute_name_is_rejected(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    result = await submit_templates(hass, setup_device, {"icon": "{{ value }}"})

    assert result["errors"] == {CONF_ATTRIBUTE_TEMPLATES: "attribute_name_reserved"}
    assert result["description_placeholders"]["attribute"] == "icon"


async def test_attribute_templates_must_be_name_template_pairs(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    result = await submit_templates(hass, setup_device, ["{{ value }}"])

    assert result["errors"] == {CONF_ATTRIBUTE_TEMPLATES: "attribute_templates_invalid"}


async def test_add_from_source_takes_attribute_templates_too(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([])
    result = await reconfigure(hass, entry)
    result = await choose(hass, result["flow_id"], "add_from_source")

    result = await submit(
        hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE, CONF_ATTRIBUTE_TEMPLATES: ["x"]}
    )
    assert result["step_id"] == "add_from_source"
    assert result["errors"] == {CONF_ATTRIBUTE_TEMPLATES: "attribute_templates_invalid"}

    result = await submit(
        hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE, CONF_ATTRIBUTE_TEMPLATES: TEMPLATES}
    )
    result = await submit(hass, result["flow_id"], BASICS)
    await save(hass, result)

    assert saved_entities(entry) == [stored(**{CONF_ATTRIBUTE_TEMPLATES: TEMPLATES})]


async def test_editing_prefills_and_clearing_removes_the_templates(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device(
        [
            {CONF_ID: "running", CONF_SOURCE_ENTITY: SOURCE, CONF_ATTRIBUTE_TEMPLATES: TEMPLATES}
            | BASICS
        ]
    )
    result = await reconfigure(hass, entry)
    result = await choose(hass, result["flow_id"], "edit_entity")
    result = await submit(hass, result["flow_id"], {"virtual_entity": "running"})
    result = await submit(hass, result["flow_id"], BASICS)
    assert suggested(result)[CONF_ATTRIBUTE_TEMPLATES] == TEMPLATES

    result = await submit(hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE})
    await save(hass, result)

    assert saved_entities(entry) == [{CONF_ID: "running", CONF_SOURCE_ENTITY: SOURCE} | BASICS]
