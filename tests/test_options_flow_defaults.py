"""The options flow suggests settings based on the source entity."""

from typing import Any
from unittest.mock import ANY

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult, FlowResultType

from custom_components.virtual_device.const import (
    CONF_ACTION_SET,
    CONF_DEVICE_CLASS,
    CONF_ENTITIES,
    CONF_ID,
    CONF_MAX,
    CONF_MIN,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
    CONF_STATE_CLASS,
    CONF_STEP,
    CONF_UNIT,
    CONF_VALUE_TEMPLATE,
)

from .conftest import SetupDevice
from .test_options_flow import choose, submit, suggested

TARGET = "number.heatpump_target"
TARGET_STATE = {
    "friendly_name": "Heat pump target",
    "min": 10,
    "max": 30,
    "step": 0.5,
    "unit_of_measurement": "°C",
}
RANGE = {CONF_MIN: 10, CONF_MAX: 30, CONF_STEP: 0.5, CONF_UNIT: "°C"}


async def start(hass: HomeAssistant, entry_id: str, menu_entry: str) -> FlowResult:
    result = await hass.config_entries.options.async_init(entry_id)
    return await choose(hass, result["flow_id"], menu_entry)


async def test_add_from_source_asks_for_the_source_first(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([])

    result = await start(hass, entry.entry_id, "add_from_source")

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_from_source"


async def test_add_from_source_prefills_type_name_and_number_range(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(TARGET, "21.5", TARGET_STATE)
    entry = await setup_device([])
    result = await start(hass, entry.entry_id, "add_from_source")

    result = await submit(hass, result["flow_id"], {CONF_SOURCE_ENTITY: TARGET})
    assert result["step_id"] == "add_entity"
    assert suggested(result) == {CONF_PLATFORM: "number", CONF_NAME: "Heat pump target"}

    result = await submit(
        hass, result["flow_id"], {CONF_PLATFORM: "number", CONF_NAME: "Heat pump target"}
    )
    assert result["step_id"] == "entity_details"  # the source is not asked again
    assert suggested(result) == RANGE

    action = [{"action": "test.set"}]
    result = await submit(hass, result["flow_id"], {**RANGE, CONF_ACTION_SET: action})
    result = await choose(hass, result["flow_id"], "save")

    assert result["data"][CONF_ENTITIES] == [
        {
            CONF_ID: ANY,
            CONF_PLATFORM: "number",
            CONF_NAME: "Heat pump target",
            CONF_SOURCE_ENTITY: TARGET,
            CONF_ACTION_SET: action,
            **RANGE,
        }
    ]


async def test_add_from_source_prefills_sensor_unit_and_classes(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(
        "sensor.outside",
        "3.2",
        {
            "unit_of_measurement": "°C",
            "device_class": "temperature",
            "state_class": "measurement",
        },
    )
    entry = await setup_device([])
    result = await start(hass, entry.entry_id, "add_from_source")
    result = await submit(hass, result["flow_id"], {CONF_SOURCE_ENTITY: "sensor.outside"})

    result = await submit(hass, result["flow_id"], {CONF_PLATFORM: "sensor", CONF_NAME: "Outside"})

    assert suggested(result) == {
        CONF_UNIT: "°C",
        CONF_DEVICE_CLASS: "temperature",
        CONF_STATE_CLASS: "measurement",
    }


async def test_add_from_source_keeps_the_template(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set("sensor.status", "18 - In Betrieb")
    entry = await setup_device([])
    result = await start(hass, entry.entry_id, "add_from_source")
    template = "{{ value.split(' - ', 1)[-1] }}"
    result = await submit(
        hass,
        result["flow_id"],
        {CONF_SOURCE_ENTITY: "sensor.status", CONF_VALUE_TEMPLATE: template},
    )

    result = await submit(
        hass, result["flow_id"], {CONF_PLATFORM: "binary_sensor", CONF_NAME: "On"}
    )
    result = await choose(hass, result["flow_id"], "save")

    assert result["data"][CONF_ENTITIES][0][CONF_VALUE_TEMPLATE] == template


async def test_add_from_source_with_a_button_does_not_keep_the_source(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(TARGET, "21.5", TARGET_STATE)
    entry = await setup_device([])
    result = await start(hass, entry.entry_id, "add_from_source")
    result = await submit(hass, result["flow_id"], {CONF_SOURCE_ENTITY: TARGET})

    result = await submit(hass, result["flow_id"], {CONF_PLATFORM: "button", CONF_NAME: "Go"})
    result = await submit(hass, result["flow_id"], {})
    result = await choose(hass, result["flow_id"], "save")

    assert CONF_SOURCE_ENTITY not in result["data"][CONF_ENTITIES][0]


async def test_add_from_unknown_source_has_no_suggestions(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([])
    result = await start(hass, entry.entry_id, "add_from_source")

    result = await submit(hass, result["flow_id"], {CONF_SOURCE_ENTITY: "sensor.not_there"})

    assert suggested(result) == {CONF_PLATFORM: "sensor", CONF_NAME: ""}


async def test_manual_add_prefills_the_details_from_the_source(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(TARGET, "21.5", TARGET_STATE)
    entry = await setup_device([])
    result = await start(hass, entry.entry_id, "add_entity")
    result = await submit(hass, result["flow_id"], {CONF_PLATFORM: "number", CONF_NAME: "Target"})

    result = await submit(hass, result["flow_id"], {CONF_SOURCE_ENTITY: TARGET})

    assert result["step_id"] == "entity_details"
    assert suggested(result) == RANGE


async def test_editing_does_not_overwrite_stored_settings_with_source_values(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(TARGET, "21.5", TARGET_STATE)
    stored: dict[str, Any] = {
        CONF_ID: "a",
        CONF_PLATFORM: "number",
        CONF_NAME: "Target",
        CONF_SOURCE_ENTITY: TARGET,
        CONF_MIN: 0,
        CONF_MAX: 50,
        CONF_STEP: 1,
    }
    entry = await setup_device([stored])
    result = await start(hass, entry.entry_id, "edit_entity")
    result = await submit(hass, result["flow_id"], {"virtual_entity": "a"})
    result = await submit(hass, result["flow_id"], {CONF_PLATFORM: "number", CONF_NAME: "Target"})
    result = await submit(hass, result["flow_id"], {CONF_SOURCE_ENTITY: TARGET})

    assert suggested(result) == {CONF_MIN: 0, CONF_MAX: 50, CONF_STEP: 1}
