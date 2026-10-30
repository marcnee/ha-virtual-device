"""The source forms ask which attributes of the source are copied."""

from typing import Any
from unittest.mock import ANY

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

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


def stored(**extra: Any) -> dict[str, Any]:
    return {CONF_ID: ANY, CONF_SOURCE_ENTITY: SOURCE} | BASICS | extra


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


async def test_selected_attributes_are_stored(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([])
    result = await source_form(hass, entry, BASICS)

    result = await submit(
        hass,
        result["flow_id"],
        {
            CONF_SOURCE_ENTITY: SOURCE,
            CONF_COPY_ATTRIBUTES: "selected",
            CONF_ATTRIBUTE_NAMES: ["error_code", "last_run"],
        },
    )
    await save(hass, result)

    assert saved_entities(entry) == [
        stored(
            **{CONF_COPY_ATTRIBUTES: "selected", CONF_ATTRIBUTE_NAMES: ["error_code", "last_run"]}
        )
    ]


async def test_selected_without_names_is_an_error(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([])
    result = await source_form(hass, entry, BASICS)

    result = await submit(
        hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE, CONF_COPY_ATTRIBUTES: "selected"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "entity_source"
    assert result["errors"] == {CONF_ATTRIBUTE_NAMES: "attribute_names_required"}
    assert suggested(result)[CONF_SOURCE_ENTITY] == SOURCE


async def test_names_are_dropped_unless_selected_is_chosen(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([])
    result = await source_form(hass, entry, BASICS)

    result = await submit(
        hass,
        result["flow_id"],
        {
            CONF_SOURCE_ENTITY: SOURCE,
            CONF_COPY_ATTRIBUTES: "all",
            CONF_ATTRIBUTE_NAMES: ["error_code"],
        },
    )
    await save(hass, result)

    assert saved_entities(entry) == [stored(**{CONF_COPY_ATTRIBUTES: "all"})]


async def test_add_from_source_asks_for_the_attributes_too(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([])
    result = await reconfigure(hass, entry)
    result = await choose(hass, result["flow_id"], "add_from_source")

    result = await submit(
        hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE, CONF_COPY_ATTRIBUTES: "selected"}
    )

    assert result["step_id"] == "add_from_source"
    assert result["errors"] == {CONF_ATTRIBUTE_NAMES: "attribute_names_required"}

    result = await submit(
        hass,
        result["flow_id"],
        {
            CONF_SOURCE_ENTITY: SOURCE,
            CONF_COPY_ATTRIBUTES: "selected",
            CONF_ATTRIBUTE_NAMES: ["error_code"],
        },
    )
    result = await submit(hass, result["flow_id"], BASICS)
    await save(hass, result)

    assert saved_entities(entry) == [
        stored(**{CONF_COPY_ATTRIBUTES: "selected", CONF_ATTRIBUTE_NAMES: ["error_code"]})
    ]


async def test_editing_prefills_the_chosen_attributes(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device(
        [
            {
                CONF_ID: "running",
                CONF_SOURCE_ENTITY: SOURCE,
                CONF_COPY_ATTRIBUTES: "selected",
                CONF_ATTRIBUTE_NAMES: ["error_code"],
            }
            | BASICS
        ]
    )
    result = await reconfigure(hass, entry)
    result = await choose(hass, result["flow_id"], "edit_entity")
    result = await submit(hass, result["flow_id"], {"virtual_entity": "running"})
    result = await submit(hass, result["flow_id"], BASICS)

    assert result["step_id"] == "entity_source"
    assert suggested(result)[CONF_COPY_ATTRIBUTES] == "selected"
    assert suggested(result)[CONF_ATTRIBUTE_NAMES] == ["error_code"]


async def test_changing_to_a_button_drops_the_source_and_its_attributes(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device(
        [
            {
                CONF_ID: "running",
                CONF_SOURCE_ENTITY: SOURCE,
                CONF_COPY_ATTRIBUTES: "selected",
                CONF_ATTRIBUTE_NAMES: ["error_code"],
            }
            | BASICS
        ]
    )
    result = await reconfigure(hass, entry)
    result = await choose(hass, result["flow_id"], "edit_entity")
    result = await submit(hass, result["flow_id"], {"virtual_entity": "running"})
    result = await submit(hass, result["flow_id"], {CONF_PLATFORM: "button", CONF_NAME: "Running"})
    result = await submit(hass, result["flow_id"], {})
    await save(hass, result)

    assert saved_entities(entry) == [
        {CONF_ID: "running", CONF_PLATFORM: "button", CONF_NAME: "Running"}
    ]
