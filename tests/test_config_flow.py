"""Config flow: creating a virtual device."""

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.virtual_device.const import CONF_DEVICE_NAME, CONF_ENTITIES, DOMAIN


async def test_user_flow_creates_empty_virtual_device(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_DEVICE_NAME: "Heat pump"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Heat pump"
    assert result["data"] == {CONF_DEVICE_NAME: "Heat pump"}
    assert result["options"] == {CONF_ENTITIES: []}
