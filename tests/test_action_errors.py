"""Broken or failing actions must not harm the rest of the virtual device."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceNotFound
from homeassistant.helpers import entity_registry as er

from custom_components.virtual_device.const import (
    CONF_ACTION_OFF,
    CONF_ACTION_ON,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
)

from .conftest import SetupDevice

SOURCE = "sensor.heatpump_mode"


def switch(**extra: object) -> dict[str, object]:
    return {
        CONF_ID: "power",
        CONF_PLATFORM: "switch",
        CONF_NAME: "Power",
        CONF_SOURCE_ENTITY: SOURCE,
        **extra,
    }


async def test_error_of_the_source_integration_reaches_the_caller(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "off")
    await setup_device([switch(**{CONF_ACTION_ON: [{"action": "test.does_not_exist"}]})])

    with pytest.raises(ServiceNotFound):
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": "switch.heat_pump_power"}, blocking=True
        )


async def test_invalid_action_config_only_disables_that_command(
    hass: HomeAssistant, setup_device: SetupDevice, caplog: pytest.LogCaptureFixture
) -> None:
    hass.states.async_set(SOURCE, "off")
    other = {
        CONF_ID: "status",
        CONF_PLATFORM: "sensor",
        CONF_NAME: "Status",
        CONF_SOURCE_ENTITY: SOURCE,
    }

    await setup_device(
        [
            switch(**{CONF_ACTION_ON: [{"bogus": 1}], CONF_ACTION_OFF: [{"action": "test.off"}]}),
            other,
        ]
    )

    assert hass.states.get("sensor.heat_pump_status").state == "off"
    assert er.async_get(hass).async_get("switch.heat_pump_power") is not None
    assert "Invalid action" in caplog.text
    with pytest.raises(HomeAssistantError, match="no action"):
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": "switch.heat_pump_power"}, blocking=True
        )
