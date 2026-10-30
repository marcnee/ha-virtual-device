"""Options flow: managing the entities of a virtual device."""

from typing import Any
from unittest.mock import ANY

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult, FlowResultType, InvalidData

from custom_components.virtual_device.const import (
    CONF_ACTION_PRESS,
    CONF_ENTITIES,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ATTRIBUTE,
    CONF_SOURCE_ENTITY,
    CONF_VALUE_TEMPLATE,
)

from .conftest import SetupDevice

SOURCE = "sensor.heatpump_status"
STRIP_CODE = "{{ value.split(' - ', 1)[-1] }}"


async def choose(hass: HomeAssistant, flow_id: str, step: str) -> FlowResult:
    """Pick a menu entry."""
    return await hass.config_entries.options.async_configure(flow_id, {"next_step_id": step})


async def submit(hass: HomeAssistant, flow_id: str, user_input: dict[str, Any]) -> FlowResult:
    return await hass.config_entries.options.async_configure(flow_id, user_input)


async def test_menu_offers_add_and_save_for_an_empty_device(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([])

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.MENU
    assert result["menu_options"] == ["add_entity", "save"]


async def test_add_sensor_with_template(hass: HomeAssistant, setup_device: SetupDevice) -> None:
    entry = await setup_device([])
    result = await hass.config_entries.options.async_init(entry.entry_id)

    result = await choose(hass, result["flow_id"], "add_entity")
    assert result["step_id"] == "add_entity"
    result = await submit(hass, result["flow_id"], {CONF_PLATFORM: "sensor", CONF_NAME: "Status"})
    assert result["step_id"] == "entity_source"
    result = await submit(
        hass,
        result["flow_id"],
        {CONF_SOURCE_ENTITY: SOURCE, CONF_VALUE_TEMPLATE: STRIP_CODE},
    )
    assert result["type"] is FlowResultType.MENU
    assert result["menu_options"] == ["add_entity", "edit_entity", "remove_entity", "save"]
    result = await choose(hass, result["flow_id"], "save")

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_ENTITIES: [
            {
                CONF_ID: ANY,
                CONF_PLATFORM: "sensor",
                CONF_NAME: "Status",
                CONF_SOURCE_ENTITY: SOURCE,
                CONF_VALUE_TEMPLATE: STRIP_CODE,
            }
        ]
    }


async def test_saved_entity_appears_in_home_assistant(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - In Betrieb")
    entry = await setup_device([])
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await choose(hass, result["flow_id"], "add_entity")
    result = await submit(hass, result["flow_id"], {CONF_PLATFORM: "sensor", CONF_NAME: "Status"})
    result = await submit(
        hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE, CONF_VALUE_TEMPLATE: STRIP_CODE}
    )
    await choose(hass, result["flow_id"], "save")
    await hass.async_block_till_done()

    assert hass.states.get("sensor.heat_pump_status").state == "In Betrieb"


async def test_invalid_template_is_rejected(hass: HomeAssistant, setup_device: SetupDevice) -> None:
    entry = await setup_device([])
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await choose(hass, result["flow_id"], "add_entity")
    result = await submit(hass, result["flow_id"], {CONF_PLATFORM: "sensor", CONF_NAME: "Status"})

    with pytest.raises(InvalidData) as error:
        await submit(
            hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE, CONF_VALUE_TEMPLATE: "{{ value"}
        )

    assert CONF_VALUE_TEMPLATE in error.value.schema_errors


async def test_button_skips_the_source_step(hass: HomeAssistant, setup_device: SetupDevice) -> None:
    entry = await setup_device([])
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await choose(hass, result["flow_id"], "add_entity")

    result = await submit(hass, result["flow_id"], {CONF_PLATFORM: "button", CONF_NAME: "Reset"})
    assert result["step_id"] == "entity_details"
    action = [{"action": "test.reset"}]
    result = await submit(hass, result["flow_id"], {CONF_ACTION_PRESS: action})
    result = await choose(hass, result["flow_id"], "save")

    assert result["data"][CONF_ENTITIES] == [
        {CONF_ID: ANY, CONF_PLATFORM: "button", CONF_NAME: "Reset", CONF_ACTION_PRESS: action}
    ]


async def test_nothing_is_saved_before_save_is_chosen(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([])
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await choose(hass, result["flow_id"], "add_entity")
    result = await submit(hass, result["flow_id"], {CONF_PLATFORM: "sensor", CONF_NAME: "Status"})
    await submit(hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE})

    assert entry.options == {CONF_ENTITIES: []}


def stored(**extra: Any) -> dict[str, Any]:
    return {
        CONF_ID: "a",
        CONF_PLATFORM: "sensor",
        CONF_NAME: "Status",
        CONF_SOURCE_ENTITY: SOURCE,
        CONF_VALUE_TEMPLATE: STRIP_CODE,
        **extra,
    }


def suggested(result: FlowResult) -> dict[str, Any]:
    """Prefilled values of a form (suggested values and defaults)."""
    values = {}
    for key in result["data_schema"].schema:
        if key.description and "suggested_value" in key.description:
            values[str(key)] = key.description["suggested_value"]
        elif callable(key.default):
            values[str(key)] = key.default()
    return values


async def test_remove_entities(hass: HomeAssistant, setup_device: SetupDevice) -> None:
    entry = await setup_device([stored(), stored(**{CONF_ID: "b", CONF_NAME: "Second"})])
    result = await hass.config_entries.options.async_init(entry.entry_id)

    result = await choose(hass, result["flow_id"], "remove_entity")
    assert result["step_id"] == "remove_entity"
    result = await submit(hass, result["flow_id"], {"virtual_entity": ["a"]})
    assert result["type"] is FlowResultType.MENU
    result = await choose(hass, result["flow_id"], "save")

    assert [e[CONF_ID] for e in result["data"][CONF_ENTITIES]] == ["b"]


async def test_editing_prefills_the_forms_and_keeps_the_id(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([stored()])
    result = await hass.config_entries.options.async_init(entry.entry_id)

    result = await choose(hass, result["flow_id"], "edit_entity")
    assert result["step_id"] == "edit_entity"
    result = await submit(hass, result["flow_id"], {"virtual_entity": "a"})
    assert result["step_id"] == "add_entity"
    assert suggested(result) == {CONF_PLATFORM: "sensor", CONF_NAME: "Status"}
    result = await submit(hass, result["flow_id"], {CONF_PLATFORM: "sensor", CONF_NAME: "Renamed"})
    assert result["step_id"] == "entity_source"
    assert suggested(result) == {
        CONF_SOURCE_ENTITY: SOURCE,
        CONF_SOURCE_ATTRIBUTE: None,
        CONF_VALUE_TEMPLATE: STRIP_CODE,
    }
    result = await submit(hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE})
    result = await choose(hass, result["flow_id"], "save")

    assert result["data"][CONF_ENTITIES] == [
        {CONF_ID: "a", CONF_PLATFORM: "sensor", CONF_NAME: "Renamed", CONF_SOURCE_ENTITY: SOURCE}
    ]


async def test_changing_the_platform_keeps_the_source_settings(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([stored()])
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await choose(hass, result["flow_id"], "edit_entity")
    result = await submit(hass, result["flow_id"], {"virtual_entity": "a"})

    result = await submit(
        hass, result["flow_id"], {CONF_PLATFORM: "binary_sensor", CONF_NAME: "Status"}
    )
    assert suggested(result)[CONF_VALUE_TEMPLATE] == STRIP_CODE
    result = await submit(
        hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE, CONF_VALUE_TEMPLATE: STRIP_CODE}
    )
    result = await choose(hass, result["flow_id"], "save")

    assert result["data"][CONF_ENTITIES][0][CONF_PLATFORM] == "binary_sensor"
    assert result["data"][CONF_ENTITIES][0][CONF_ID] == "a"
