"""A virtual entity can follow more entities than its source and read them in its templates."""

import logging

import pytest
from homeassistant.core import HomeAssistant

from custom_components.virtual_device.const import (
    CONF_ATTRIBUTE_TEMPLATES,
    CONF_EXTRA_SOURCES,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
    CONF_VALUE_TEMPLATE,
)

from .conftest import SetupDevice

TIME = "sensor.boiler_error_time"
CODE = "sensor.boiler_error_code"
ENTITY = "sensor.heat_pump_last_error"
TEMPLATE = (
    "{% set code = sources['sensor.boiler_error_code'].state %}"
    "{{ value }} - {{ code.split(' - ')[0] }} - {{ code.split(':', 1)[1] }}"
)


def last_error(**extra: object) -> dict[str, object]:
    return {
        CONF_ID: "last_error",
        CONF_PLATFORM: "sensor",
        CONF_NAME: "Last error",
        CONF_SOURCE_ENTITY: TIME,
        CONF_EXTRA_SOURCES: [CODE],
        CONF_VALUE_TEMPLATE: TEMPLATE,
    } | extra


async def test_a_value_is_made_of_the_source_and_the_extra_sources(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(TIME, "29.10.2026 11:14:00")
    hass.states.async_set(CODE, "133 - 133:Safety time exceeded")

    await setup_device([last_error()])

    assert hass.states.get(ENTITY).state == "29.10.2026 11:14:00 - 133 - Safety time exceeded"


async def test_a_change_of_an_extra_source_updates_the_entity(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(TIME, "29.10.2026 11:14:00")
    hass.states.async_set(CODE, "133 - 133:Safety time exceeded")
    await setup_device([last_error()])

    hass.states.async_set(CODE, "7 - 7:Fan blocked")
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY).state == "29.10.2026 11:14:00 - 7 - Fan blocked"


async def test_attribute_templates_follow_the_extra_sources_too(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(TIME, "t")
    hass.states.async_set(CODE, "1")
    await setup_device(
        [
            last_error(
                **{
                    CONF_VALUE_TEMPLATE: None,
                    CONF_ATTRIBUTE_TEMPLATES: {
                        "code": "{{ sources['sensor.boiler_error_code'].state }}"
                    },
                }
            )
        ]
    )

    hass.states.async_set(CODE, "2")
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY).attributes["code"] == 2


async def test_an_extra_source_that_is_missing_leaves_the_value_unknown(
    hass: HomeAssistant, setup_device: SetupDevice, caplog: pytest.LogCaptureFixture
) -> None:
    hass.states.async_set(TIME, "29.10.2026 11:14:00")

    with caplog.at_level(logging.WARNING):
        await setup_device([last_error()])

    assert hass.states.get(ENTITY).state == "unknown"
    assert "Last error" in caplog.text

    hass.states.async_set(CODE, "133 - 133:Safety time exceeded")
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY).state == "29.10.2026 11:14:00 - 133 - Safety time exceeded"


async def test_the_entity_is_unavailable_only_when_its_source_is(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(TIME, "t")
    hass.states.async_set(CODE, "1 - 1:x")
    await setup_device([last_error()])

    hass.states.async_set(CODE, "unavailable")
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY).state != "unavailable"

    hass.states.async_set(TIME, "unavailable")
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY).state == "unavailable"
