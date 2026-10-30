"""Attributes of virtual entities: copied from the source, and marking where they come from."""

from homeassistant.core import HomeAssistant

from custom_components.virtual_device.const import (
    CONF_ACTION_ON,
    CONF_ACTION_PRESS,
    CONF_ATTRIBUTE_NAMES,
    CONF_COPY_ATTRIBUTES,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ATTRIBUTE,
    CONF_SOURCE_ENTITY,
)

from .conftest import SetupDevice

SOURCE = "sensor.heatpump_status"
ACTION = [{"action": "homeassistant.update_entity", "target": {"entity_id": SOURCE}}]


def sensor(**extra: object) -> dict[str, object]:
    return {
        CONF_ID: "status",
        CONF_PLATFORM: "sensor",
        CONF_NAME: "Status",
        CONF_SOURCE_ENTITY: SOURCE,
    } | extra


async def test_source_attributes_are_not_copied_by_default(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "on", {"error_code": 7})

    await setup_device([sensor()])

    assert "error_code" not in hass.states.get("sensor.heat_pump_status").attributes


async def test_all_attributes_are_copied_and_follow_the_source(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "on", {"error_code": 7})
    await setup_device([sensor(**{CONF_COPY_ATTRIBUTES: "all"})])
    assert hass.states.get("sensor.heat_pump_status").attributes["error_code"] == 7

    hass.states.async_set(SOURCE, "on", {"error_code": 9})
    await hass.async_block_till_done()

    assert hass.states.get("sensor.heat_pump_status").attributes["error_code"] == 9


async def test_selected_attributes_are_copied(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "on", {"error_code": 7, "last_run": "yesterday"})

    await setup_device(
        [sensor(**{CONF_COPY_ATTRIBUTES: "selected", CONF_ATTRIBUTE_NAMES: ["last_run"]})]
    )

    attributes = hass.states.get("sensor.heat_pump_status").attributes
    assert attributes["last_run"] == "yesterday"
    assert "error_code" not in attributes


async def test_the_entity_names_its_source(hass: HomeAssistant, setup_device: SetupDevice) -> None:
    hass.states.async_set(SOURCE, "on")

    await setup_device([sensor()])

    attributes = hass.states.get("sensor.heat_pump_status").attributes
    assert attributes["source_entity"] == SOURCE
    assert "source_attribute" not in attributes


async def test_the_entity_names_the_source_attribute_it_reads(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "on", {"error_code": 7})

    await setup_device([sensor(**{CONF_SOURCE_ATTRIBUTE: "error_code"})])

    assert hass.states.get("sensor.heat_pump_status").attributes["source_attribute"] == "error_code"


async def test_a_copied_attribute_cannot_replace_the_marking(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "on", {"source_entity": "fake", "forwards_commands": "fake"})

    await setup_device([sensor(**{CONF_COPY_ATTRIBUTES: "all"})])

    attributes = hass.states.get("sensor.heat_pump_status").attributes
    assert attributes["source_entity"] == SOURCE
    assert "forwards_commands" not in attributes


async def test_entities_with_an_action_say_that_they_forward_commands(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set("switch.pump", "on")
    switch = {
        CONF_ID: "pump",
        CONF_PLATFORM: "switch",
        CONF_NAME: "Pump",
        CONF_SOURCE_ENTITY: "switch.pump",
        CONF_ACTION_ON: ACTION,
    }
    plain = {k: v for k, v in switch.items() if k != CONF_ACTION_ON}
    plain |= {CONF_ID: "plain", CONF_NAME: "Plain"}

    await setup_device([switch, plain])

    assert hass.states.get("switch.heat_pump_pump").attributes["forwards_commands"] is True
    assert "forwards_commands" not in hass.states.get("switch.heat_pump_plain").attributes


async def test_a_button_without_source_only_says_that_it_forwards_commands(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    button = {
        CONF_ID: "go",
        CONF_PLATFORM: "button",
        CONF_NAME: "Go",
        CONF_ACTION_PRESS: ACTION,
    }

    await setup_device([button])

    attributes = hass.states.get("button.heat_pump_go").attributes
    assert attributes["forwards_commands"] is True
    assert "source_entity" not in attributes
