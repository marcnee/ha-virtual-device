"""Config flow: setting up the service."""

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.virtual_device.const import DOMAIN

from .conftest import SetupDevices


async def test_user_flow_creates_the_service_without_devices(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Virtual Device"
    assert result["data"] == {}
    assert result["version"] == 2


async def test_the_service_can_only_be_added_once(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    await setup_devices({})

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"
