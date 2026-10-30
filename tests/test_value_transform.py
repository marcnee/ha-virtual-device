"""Transforming source values with templates and attributes."""

import pytest
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from custom_components.virtual_device.const import (
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ATTRIBUTE,
    CONF_SOURCE_ENTITY,
    CONF_VALUE_TEMPLATE,
)

from .conftest import SetupDevice

SOURCE = "sensor.heatpump_status"


def sensor(entity_id: str, name: str, **extra: str) -> dict[str, str]:
    return {
        CONF_ID: entity_id,
        CONF_PLATFORM: "sensor",
        CONF_NAME: name,
        CONF_SOURCE_ENTITY: SOURCE,
        **extra,
    }


async def test_template_strips_numeric_prefix(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - In Betrieb")

    await setup_device(
        [sensor("text", "Status", **{CONF_VALUE_TEMPLATE: "{{ value.split(' - ', 1)[-1] }}"})]
    )

    assert hass.states.get("sensor.heat_pump_status").state == "In Betrieb"


async def test_template_is_reevaluated_on_source_change(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - In Betrieb")
    await setup_device(
        [sensor("text", "Status", **{CONF_VALUE_TEMPLATE: "{{ value.split(' - ', 1)[-1] }}"})]
    )

    hass.states.async_set(SOURCE, "19 - Standby")
    await hass.async_block_till_done()

    assert hass.states.get("sensor.heat_pump_status").state == "Standby"


async def test_two_virtual_entities_from_the_same_source(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - In Betrieb")

    await setup_device(
        [
            sensor("text", "Status", **{CONF_VALUE_TEMPLATE: "{{ value.split(' - ', 1)[-1] }}"}),
            sensor("code", "Status code", **{CONF_VALUE_TEMPLATE: "{{ value.split(' - ')[0] }}"}),
        ]
    )

    assert hass.states.get("sensor.heat_pump_status").state == "In Betrieb"
    assert hass.states.get("sensor.heat_pump_status_code").state == "18"


async def test_source_attribute_is_used_instead_of_state(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "ignored", {"mode": "eco"})

    await setup_device([sensor("mode", "Mode", **{CONF_SOURCE_ATTRIBUTE: "mode"})])

    assert hass.states.get("sensor.heat_pump_mode").state == "eco"


async def test_template_can_use_attributes(hass: HomeAssistant, setup_device: SetupDevice) -> None:
    hass.states.async_set(SOURCE, "18 - In Betrieb", {"code": 18})

    await setup_device([sensor("code", "Code", **{CONF_VALUE_TEMPLATE: "{{ attributes.code }}"})])

    assert hass.states.get("sensor.heat_pump_code").state == "18"


@pytest.mark.parametrize("result", ["none", "unknown", "unavailable", ""])
async def test_template_result_without_value_is_unknown(
    hass: HomeAssistant, setup_device: SetupDevice, result: str
) -> None:
    hass.states.async_set(SOURCE, "18 - In Betrieb")

    await setup_device([sensor("text", "Status", **{CONF_VALUE_TEMPLATE: result or "{{ '' }}"})])

    assert hass.states.get("sensor.heat_pump_status").state == STATE_UNKNOWN


async def test_failing_template_gives_unknown_instead_of_raising(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "18 - In Betrieb")

    await setup_device([sensor("text", "Status", **{CONF_VALUE_TEMPLATE: "{{ 1 / 0 }}"})])

    assert hass.states.get("sensor.heat_pump_status").state == STATE_UNKNOWN


async def test_template_is_not_run_while_source_is_unknown(
    hass: HomeAssistant, setup_device: SetupDevice, caplog: pytest.LogCaptureFixture
) -> None:
    hass.states.async_set(SOURCE, STATE_UNKNOWN)

    await setup_device(
        [sensor("text", "Status", **{CONF_VALUE_TEMPLATE: "{{ value.split(' - ', 1)[-1] }}"})]
    )

    assert hass.states.get("sensor.heat_pump_status").state == STATE_UNKNOWN
    assert "Template" not in caplog.text
