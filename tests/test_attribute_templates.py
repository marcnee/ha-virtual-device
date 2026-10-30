"""Attributes of a virtual entity computed from the source with templates."""

import logging

import pytest
from homeassistant.core import HomeAssistant

from custom_components.virtual_device.const import (
    CONF_ATTRIBUTE_TEMPLATES,
    CONF_COPY_ATTRIBUTES,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ATTRIBUTE,
    CONF_SOURCE_ENTITY,
)

from .conftest import SetupDevice

SOURCE = "sensor.heatpump_status"
ENTITY = "sensor.heat_pump_status"


def sensor(templates: dict[str, str], **extra: object) -> dict[str, object]:
    return {
        CONF_ID: "status",
        CONF_PLATFORM: "sensor",
        CONF_NAME: "Status",
        CONF_SOURCE_ENTITY: SOURCE,
        CONF_ATTRIBUTE_TEMPLATES: templates,
    } | extra


async def test_a_template_creates_an_attribute_with_a_native_value(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - Running", {"error_code": 7})

    await setup_device([sensor({"next_code": "{{ attributes.error_code | int + 1 }}"})])

    assert hass.states.get(ENTITY).attributes["next_code"] == 8


async def test_templates_see_value_state_and_attributes(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - Running", {"room": "cellar"})

    await setup_device(
        [
            sensor(
                {
                    "text": "{{ value.split(' - ')[1] }}",
                    "raw": "{{ state.state }}",
                    "room_upper": "{{ attributes.room | upper }}",
                }
            )
        ]
    )

    attributes = hass.states.get(ENTITY).attributes
    assert attributes["text"] == "Running"
    assert attributes["raw"] == "18 - Running"
    assert attributes["room_upper"] == "CELLAR"


async def test_value_is_the_chosen_source_attribute(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "on", {"error_code": 7})

    await setup_device(
        [sensor({"doubled": "{{ value * 2 }}"}, **{CONF_SOURCE_ATTRIBUTE: "error_code"})]
    )

    assert hass.states.get(ENTITY).attributes["doubled"] == 14


async def test_attributes_follow_the_source(hass: HomeAssistant, setup_device: SetupDevice) -> None:
    hass.states.async_set(SOURCE, "1", {"error_code": 7})
    await setup_device([sensor({"code": "{{ attributes.error_code }}"})])

    hass.states.async_set(SOURCE, "1", {"error_code": 9})
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY).attributes["code"] == 9


async def test_a_template_wins_over_a_copied_attribute_of_the_same_name(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "1", {"error_code": 7, "other": "x"})

    await setup_device(
        [
            sensor(
                {"error_code": "{{ 'E' ~ attributes.error_code }}"}, **{CONF_COPY_ATTRIBUTES: "all"}
            )
        ]
    )

    attributes = hass.states.get(ENTITY).attributes
    assert attributes["error_code"] == "E7"
    assert attributes["other"] == "x"


async def test_a_template_without_a_value_leaves_the_attribute_out(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "1", {})

    await setup_device([sensor({"code": "{{ none }}"})])

    assert "code" not in hass.states.get(ENTITY).attributes


async def test_a_failing_template_is_logged_and_only_skips_its_attribute(
    hass: HomeAssistant, setup_device: SetupDevice, caplog: pytest.LogCaptureFixture
) -> None:
    hass.states.async_set(SOURCE, "1", {"error_code": "x"})

    with caplog.at_level(logging.WARNING):
        await setup_device(
            [sensor({"bad": "{{ attributes.error_code | int(0) / 0 }}", "ok": "{{ 1 }}"})]
        )

    attributes = hass.states.get(ENTITY).attributes
    assert "bad" not in attributes
    assert attributes["ok"] == 1
    assert "Attribute template 'bad'" in caplog.text


async def test_the_marking_cannot_be_overwritten_by_a_template(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "1", {})

    await setup_device([sensor({"source_entity": "fake"})])

    assert hass.states.get(ENTITY).attributes["source_entity"] == SOURCE
