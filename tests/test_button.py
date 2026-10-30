"""Virtual buttons."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.virtual_device.const import (
    CONF_ACTION_PRESS,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    DOMAIN,
)

from .conftest import SetupDevice

ENTITY_ID = "button.heat_pump_reset"
RESET = {
    CONF_ID: "reset",
    CONF_PLATFORM: "button",
    CONF_NAME: "Reset",
    CONF_ACTION_PRESS: [{"action": "test.reset"}],
}


async def test_pressing_runs_the_action(hass: HomeAssistant, setup_device: SetupDevice) -> None:
    calls = async_mock_service(hass, "test", "reset")
    await setup_device([RESET])

    await hass.services.async_call("button", "press", {"entity_id": ENTITY_ID}, blocking=True)

    assert len(calls) == 1


async def test_button_needs_no_source_and_is_grouped_under_the_device(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([RESET])

    entity = er.async_get(hass).async_get(ENTITY_ID)
    device = dr.async_get(hass).async_get(entity.device_id)
    assert (DOMAIN, entry.entry_id) in device.identifiers
