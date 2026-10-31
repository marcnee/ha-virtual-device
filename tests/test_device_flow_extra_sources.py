"""The source forms take extra sources, which the templates can read."""

from typing import Any
from unittest.mock import ANY

from homeassistant.core import HomeAssistant

from custom_components.virtual_device.const import (
    CONF_EXTRA_SOURCES,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
    CONF_TEST_TEMPLATE,
    CONF_VALUE_TEMPLATE,
)

from .conftest import SetupDevice
from .helpers import choose, reconfigure, save, saved_entities, source_form, submit, suggested

SOURCE = "sensor.boiler_error_time"
CODE = "sensor.boiler_error_code"
BASICS = {CONF_PLATFORM: "sensor", CONF_NAME: "Last error"}
TEMPLATE = "{{ value }} - {{ sources['sensor.boiler_error_code'].state }}"


def stored(**extra: Any) -> dict[str, Any]:
    return {CONF_ID: ANY, CONF_SOURCE_ENTITY: SOURCE} | BASICS | extra


async def test_extra_sources_are_stored_with_the_entity(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([])
    result = await source_form(hass, entry, BASICS)

    result = await submit(
        hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE, CONF_EXTRA_SOURCES: [CODE]}
    )
    await save(hass, result)

    assert saved_entities(entry) == [stored(**{CONF_EXTRA_SOURCES: [CODE]})]


async def test_no_extra_sources_are_not_stored(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([])
    result = await source_form(hass, entry, BASICS)

    result = await submit(
        hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE, CONF_EXTRA_SOURCES: []}
    )
    await save(hass, result)

    assert saved_entities(entry) == [stored()]


async def test_extra_sources_can_be_chosen_when_adding_from_a_source(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "29.10.2026")
    entry = await setup_device([])
    result = await reconfigure(hass, entry)
    result = await choose(hass, result["flow_id"], "add_from_source")

    result = await submit(
        hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE, CONF_EXTRA_SOURCES: [CODE]}
    )
    result = await submit(hass, result["flow_id"], BASICS)
    await save(hass, result)

    assert saved_entities(entry) == [stored(**{CONF_EXTRA_SOURCES: [CODE]})]


async def test_editing_prefills_and_clearing_removes_the_extra_sources(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device(
        [{CONF_ID: "last", CONF_SOURCE_ENTITY: SOURCE, CONF_EXTRA_SOURCES: [CODE]} | BASICS]
    )
    result = await reconfigure(hass, entry)
    result = await choose(hass, result["flow_id"], "edit_entity")
    result = await submit(hass, result["flow_id"], {"virtual_entity": "last"})
    result = await submit(hass, result["flow_id"], BASICS)
    assert suggested(result)[CONF_EXTRA_SOURCES] == [CODE]

    result = await submit(hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE})
    await save(hass, result)

    assert saved_entities(entry) == [{CONF_ID: "last", CONF_SOURCE_ENTITY: SOURCE} | BASICS]


async def test_the_test_of_the_templates_reads_the_extra_sources(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "29.10.2026")
    hass.states.async_set(CODE, "133")
    entry = await setup_device([])
    result = await source_form(hass, entry, BASICS)

    result = await submit(
        hass,
        result["flow_id"],
        {
            CONF_SOURCE_ENTITY: SOURCE,
            CONF_EXTRA_SOURCES: [CODE],
            CONF_VALUE_TEMPLATE: TEMPLATE,
            CONF_TEST_TEMPLATE: True,
        },
    )

    assert (
        "Result of the value template: `29.10.2026 - 133`"
        in (result["description_placeholders"]["preview"])
    )
