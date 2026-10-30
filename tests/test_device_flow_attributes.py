"""The source forms ask which attributes of the source are copied."""

from typing import Any
from unittest.mock import ANY

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult, FlowResultType

from custom_components.virtual_device.const import (
    CONF_ATTRIBUTE_NAMES,
    CONF_COPY_ATTRIBUTES,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
)

from .conftest import SetupDevice
from .helpers import choose, reconfigure, save, saved_entities, source_form, submit, suggested

SOURCE = "sensor.heatpump_status"
BASICS = {CONF_PLATFORM: "binary_sensor", CONF_NAME: "Running"}
SELECTED = {CONF_SOURCE_ENTITY: SOURCE, CONF_COPY_ATTRIBUTES: "selected"}


def stored(**extra: Any) -> dict[str, Any]:
    return {CONF_ID: ANY, CONF_SOURCE_ENTITY: SOURCE} | BASICS | extra


def offered_names(result: FlowResult) -> list[str]:
    """The attribute names the form offers as choices."""
    selector = next(
        s for key, s in result["data_schema"].schema.items() if str(key) == CONF_ATTRIBUTE_NAMES
    )
    return sorted(o if isinstance(o, str) else o["value"] for o in selector.config["options"])


async def test_copy_all_attributes_is_stored(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([])
    result = await source_form(hass, entry, BASICS)
    assert result["step_id"] == "entity_source"

    result = await submit(
        hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE, CONF_COPY_ATTRIBUTES: "all"}
    )
    await save(hass, result)

    assert saved_entities(entry) == [stored(**{CONF_COPY_ATTRIBUTES: "all"})]


async def test_selecting_attributes_offers_the_attributes_of_the_source(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(
        SOURCE, "on", {"error_code": 7, "last_run": "x", "friendly_name": "F", "icon": "mdi:x"}
    )
    entry = await setup_device([])
    result = await source_form(hass, entry, BASICS)

    result = await submit(hass, result["flow_id"], SELECTED)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_attributes"
    assert offered_names(result) == ["error_code", "last_run"]  # no reserved attributes


async def test_other_attribute_names_can_be_typed_in(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([])  # the source does not exist yet
    result = await source_form(hass, entry, BASICS)

    result = await submit(hass, result["flow_id"], SELECTED)

    assert offered_names(result) == []
    selector = next(iter(result["data_schema"].schema.values()))
    assert selector.config["custom_value"] is True
    result = await submit(hass, result["flow_id"], {CONF_ATTRIBUTE_NAMES: ["later_attribute"]})
    await save(hass, result)
    assert saved_entities(entry) == [
        stored(**{CONF_COPY_ATTRIBUTES: "selected", CONF_ATTRIBUTE_NAMES: ["later_attribute"]})
    ]


async def test_selected_attributes_are_stored(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "on", {"error_code": 7, "last_run": "x"})
    entry = await setup_device([])
    result = await source_form(hass, entry, BASICS)
    result = await submit(hass, result["flow_id"], SELECTED)

    result = await submit(hass, result["flow_id"], {CONF_ATTRIBUTE_NAMES: ["error_code"]})
    await save(hass, result)

    assert saved_entities(entry) == [
        stored(**{CONF_COPY_ATTRIBUTES: "selected", CONF_ATTRIBUTE_NAMES: ["error_code"]})
    ]


async def test_selecting_no_attribute_is_an_error(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([])
    result = await source_form(hass, entry, BASICS)
    result = await submit(hass, result["flow_id"], SELECTED)

    result = await submit(hass, result["flow_id"], {CONF_ATTRIBUTE_NAMES: []})

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_attributes"
    assert result["errors"] == {CONF_ATTRIBUTE_NAMES: "attribute_names_required"}


async def test_add_from_source_continues_with_the_basics_after_the_attributes(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "on", {"error_code": 7})
    entry = await setup_device([])
    result = await reconfigure(hass, entry)
    result = await choose(hass, result["flow_id"], "add_from_source")

    result = await submit(hass, result["flow_id"], SELECTED)
    assert result["step_id"] == "select_attributes"
    assert offered_names(result) == ["error_code"]
    result = await submit(hass, result["flow_id"], {CONF_ATTRIBUTE_NAMES: ["error_code"]})
    assert result["step_id"] == "add_entity"
    result = await submit(hass, result["flow_id"], BASICS)
    await save(hass, result)

    assert saved_entities(entry) == [
        stored(**{CONF_COPY_ATTRIBUTES: "selected", CONF_ATTRIBUTE_NAMES: ["error_code"]})
    ]


def selected_entity() -> dict[str, Any]:
    return {
        CONF_ID: "running",
        CONF_SOURCE_ENTITY: SOURCE,
        CONF_COPY_ATTRIBUTES: "selected",
        CONF_ATTRIBUTE_NAMES: ["error_code"],
    } | BASICS


async def edit_to_source_form(hass: HomeAssistant, entry: Any) -> FlowResult:
    result = await reconfigure(hass, entry)
    result = await choose(hass, result["flow_id"], "edit_entity")
    result = await submit(hass, result["flow_id"], {"virtual_entity": "running"})
    return await submit(hass, result["flow_id"], BASICS)


async def test_editing_prefills_the_chosen_attributes(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([selected_entity()])
    result = await edit_to_source_form(hass, entry)
    assert suggested(result)[CONF_COPY_ATTRIBUTES] == "selected"

    result = await submit(hass, result["flow_id"], SELECTED)

    assert result["step_id"] == "select_attributes"
    assert suggested(result)[CONF_ATTRIBUTE_NAMES] == ["error_code"]


async def test_names_are_dropped_when_no_longer_selected(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([selected_entity()])
    result = await edit_to_source_form(hass, entry)

    result = await submit(
        hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE, CONF_COPY_ATTRIBUTES: "all"}
    )
    await save(hass, result)

    assert saved_entities(entry) == [
        {CONF_ID: "running", CONF_COPY_ATTRIBUTES: "all", CONF_SOURCE_ENTITY: SOURCE} | BASICS
    ]


async def test_changing_to_a_button_drops_the_source_and_its_attributes(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([selected_entity()])
    result = await reconfigure(hass, entry)
    result = await choose(hass, result["flow_id"], "edit_entity")
    result = await submit(hass, result["flow_id"], {"virtual_entity": "running"})
    result = await submit(hass, result["flow_id"], {CONF_PLATFORM: "button", CONF_NAME: "Running"})
    result = await submit(hass, result["flow_id"], {})
    await save(hass, result)

    assert saved_entities(entry) == [
        {CONF_ID: "running", CONF_PLATFORM: "button", CONF_NAME: "Running"}
    ]
