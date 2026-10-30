"""Optional icon per virtual entity."""

from typing import Any
from unittest.mock import ANY

from homeassistant.core import HomeAssistant

from custom_components.virtual_device.const import (
    CONF_ICON,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
)

from .conftest import SetupDevice
from .helpers import choose, reconfigure, saved_entities, submit, suggested

SOURCE = "sensor.heatpump_status"
STATUS = {
    CONF_ID: "status",
    CONF_PLATFORM: "sensor",
    CONF_NAME: "Status",
    CONF_SOURCE_ENTITY: SOURCE,
}


async def test_configured_icon_is_shown(hass: HomeAssistant, setup_device: SetupDevice) -> None:
    hass.states.async_set(SOURCE, "on")

    await setup_device([{**STATUS, CONF_ICON: "mdi:heat-pump"}])

    assert hass.states.get("sensor.heat_pump_status").attributes["icon"] == "mdi:heat-pump"


async def test_icon_is_set_in_the_basics_form(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([])
    result = await reconfigure(hass, entry)
    result = await choose(hass, result["flow_id"], "add_entity")

    result = await submit(
        hass,
        result["flow_id"],
        {CONF_PLATFORM: "binary_sensor", CONF_NAME: "Running", CONF_ICON: "mdi:fan"},
    )
    result = await submit(hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE})
    result = await choose(hass, result["flow_id"], "save")

    assert saved_entities(entry)[0] == {
        CONF_ID: ANY,
        CONF_PLATFORM: "binary_sensor",
        CONF_NAME: "Running",
        CONF_ICON: "mdi:fan",
        CONF_SOURCE_ENTITY: SOURCE,
    }


async def test_icon_can_be_edited_and_removed(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([{**STATUS, CONF_ICON: "mdi:fan"}])
    result = await reconfigure(hass, entry)
    result = await choose(hass, result["flow_id"], "edit_entity")
    result = await submit(hass, result["flow_id"], {"virtual_entity": "status"})
    assert suggested(result)[CONF_ICON] == "mdi:fan"

    changes: dict[str, Any] = {CONF_PLATFORM: "binary_sensor", CONF_NAME: "Status"}
    result = await submit(hass, result["flow_id"], changes)
    result = await submit(hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE})
    result = await choose(hass, result["flow_id"], "save")

    assert CONF_ICON not in saved_entities(entry)[0]
