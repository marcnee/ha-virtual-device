"""The source forms can test the templates with the current state of the source."""

from unittest.mock import ANY

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult, FlowResultType

from custom_components.virtual_device.const import (
    CONF_ATTRIBUTE_TEMPLATES,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
    CONF_TEST_TEMPLATE,
    CONF_VALUE_TEMPLATE,
)
from custom_components.virtual_device.template_preview import NOTHING

from .conftest import SetupDevice
from .helpers import choose, reconfigure, save, saved_entities, source_form, submit

SOURCE = "sensor.heatpump_status"
BASICS = {CONF_PLATFORM: "binary_sensor", CONF_NAME: "Running"}
TEMPLATE = "{{ value.split(' - ')[-1] }}"
INPUT = {CONF_SOURCE_ENTITY: SOURCE, CONF_VALUE_TEMPLATE: TEMPLATE}
PREVIEW_KEYS = {"source_value", "value_result", "attribute_results"}


def preview(result: FlowResult) -> dict[str, str]:
    placeholders = result["description_placeholders"]
    return {key: placeholders[key] for key in PREVIEW_KEYS}


async def start_from_source(hass: HomeAssistant, entry) -> FlowResult:
    result = await reconfigure(hass, entry)
    return await choose(hass, result["flow_id"], "add_from_source")


async def test_the_source_form_offers_the_test_and_shows_nothing_at_first(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([])

    result = await start_from_source(hass, entry)

    assert CONF_TEST_TEMPLATE in {str(key) for key in result["data_schema"].schema}
    assert preview(result) == dict.fromkeys(PREVIEW_KEYS, NOTHING)


async def test_testing_shows_the_result_and_keeps_the_form_open(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - Running")
    entry = await setup_device([])
    result = await start_from_source(hass, entry)

    result = await submit(hass, result["flow_id"], {**INPUT, CONF_TEST_TEMPLATE: True})

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_from_source"
    assert not result["errors"]
    assert preview(result) == {
        "source_value": "`18 - Running`",
        "value_result": "`Running`",
        "attribute_results": NOTHING,
    }


async def test_the_entered_values_stay_in_the_form_after_testing(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - Running")
    entry = await setup_device([])
    result = await start_from_source(hass, entry)

    result = await submit(hass, result["flow_id"], {**INPUT, CONF_TEST_TEMPLATE: True})

    suggestions = {
        str(key): key.description["suggested_value"]
        for key in result["data_schema"].schema
        if key.description and "suggested_value" in key.description
    }
    assert suggestions[CONF_SOURCE_ENTITY] == SOURCE
    assert suggestions[CONF_VALUE_TEMPLATE] == TEMPLATE


async def test_continuing_after_a_test_does_not_store_the_test(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - Running")
    entry = await setup_device([])
    result = await start_from_source(hass, entry)
    result = await submit(hass, result["flow_id"], {**INPUT, CONF_TEST_TEMPLATE: True})

    result = await submit(hass, result["flow_id"], INPUT)
    assert result["step_id"] == "add_entity"
    result = await submit(hass, result["flow_id"], BASICS)
    await save(hass, result)

    assert saved_entities(entry) == [{CONF_ID: ANY, **BASICS, **INPUT}]


async def test_the_test_works_in_the_source_form_of_a_manually_added_entity(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - Running", {"error_code": 7})
    entry = await setup_device([])
    result = await source_form(hass, entry, BASICS)
    assert result["step_id"] == "entity_source"
    templates = {"next_code": "{{ attributes.error_code | int + 1 }}"}

    result = await submit(
        hass,
        result["flow_id"],
        {**INPUT, CONF_ATTRIBUTE_TEMPLATES: templates, CONF_TEST_TEMPLATE: True},
    )

    assert result["step_id"] == "entity_source"
    assert preview(result)["value_result"] == "`Running`"
    assert preview(result)["attribute_results"] == "`next_code`: `8`"
    result = await submit(hass, result["flow_id"], {**INPUT, CONF_ATTRIBUTE_TEMPLATES: templates})
    await save(hass, result)
    assert saved_entities(entry) == [
        {CONF_ID: ANY, **BASICS, **INPUT, CONF_ATTRIBUTE_TEMPLATES: templates}
    ]


async def test_a_template_with_an_error_is_shown_in_the_result(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "abc")
    entry = await setup_device([])
    result = await start_from_source(hass, entry)

    result = await submit(
        hass,
        result["flow_id"],
        {
            CONF_SOURCE_ENTITY: SOURCE,
            CONF_VALUE_TEMPLATE: "{{ value | int(strict=True) }}",
            CONF_TEST_TEMPLATE: True,
        },
    )

    assert result["step_id"] == "add_from_source"
    assert preview(result)["value_result"].startswith("⚠ ")


async def test_invalid_attribute_templates_show_their_error_and_still_a_preview(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - Running")
    entry = await setup_device([])
    result = await start_from_source(hass, entry)

    result = await submit(
        hass,
        result["flow_id"],
        {**INPUT, CONF_ATTRIBUTE_TEMPLATES: {"icon": "{{ 1 }}"}, CONF_TEST_TEMPLATE: True},
    )

    assert result["errors"] == {CONF_ATTRIBUTE_TEMPLATES: "attribute_name_reserved"}
    assert result["description_placeholders"]["attribute"] == "icon"
    assert preview(result)["source_value"] == "`18 - Running`"


async def test_a_source_that_does_not_exist_can_be_tested_and_shows_nothing(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([])
    result = await start_from_source(hass, entry)

    result = await submit(hass, result["flow_id"], {**INPUT, CONF_TEST_TEMPLATE: True})

    assert result["step_id"] == "add_from_source"
    assert preview(result) == dict.fromkeys(PREVIEW_KEYS, NOTHING)


async def test_editing_shows_the_preview_of_the_stored_templates_at_once(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - Running")
    entry = await setup_device([{CONF_ID: "a", **BASICS, **INPUT}])
    result = await reconfigure(hass, entry)
    result = await choose(hass, result["flow_id"], "edit_entity")
    result = await submit(hass, result["flow_id"], {"virtual_entity": "a"})

    result = await submit(hass, result["flow_id"], BASICS)

    assert result["step_id"] == "entity_source"
    assert preview(result)["value_result"] == "`Running`"
