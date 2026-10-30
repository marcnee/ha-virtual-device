"""Adding a virtual device to the service."""

from unittest.mock import ANY

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.virtual_device.const import (
    CONF_DEVICE_NAME,
    CONF_ENTITIES,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
)

from .conftest import SetupDevices
from .helpers import choose, new_device, saved_entities, submit

SOURCE = "sensor.boiler_temperature"


async def test_new_device_asks_for_its_name_then_shows_the_menu(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    entry = await setup_devices({})

    result = await new_device(hass, entry)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    result = await submit(hass, result["flow_id"], {CONF_DEVICE_NAME: "Boiler"})

    assert result["type"] is FlowResultType.MENU
    assert result["menu_options"] == ["add_from_source", "add_entity", "save"]


async def test_new_device_without_entities_is_created(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    entry = await setup_devices({})
    result = await new_device(hass, entry)
    result = await submit(hass, result["flow_id"], {CONF_DEVICE_NAME: "Boiler"})

    result = await choose(hass, result["flow_id"], "save")

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Boiler"
    assert saved_entities(entry, "Boiler") == []


async def test_new_device_is_created_together_with_its_entities(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    hass.states.async_set(SOURCE, "62.5")
    entry = await setup_devices({})
    result = await new_device(hass, entry)
    result = await submit(hass, result["flow_id"], {CONF_DEVICE_NAME: "Boiler"})
    result = await choose(hass, result["flow_id"], "add_entity")
    result = await submit(hass, result["flow_id"], {CONF_PLATFORM: "sensor", CONF_NAME: "Temp"})
    result = await submit(hass, result["flow_id"], {CONF_SOURCE_ENTITY: SOURCE})
    result = await submit(hass, result["flow_id"], {})

    await choose(hass, result["flow_id"], "save")
    await hass.async_block_till_done()

    assert saved_entities(entry, "Boiler") == [
        {CONF_ID: ANY, CONF_PLATFORM: "sensor", CONF_NAME: "Temp", CONF_SOURCE_ENTITY: SOURCE}
    ]
    assert hass.states.get("sensor.boiler_temp").state == "62.5"


async def test_a_second_device_can_be_added_to_the_same_service(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    entry = await setup_devices({"Heat pump": []})
    result = await new_device(hass, entry)
    result = await submit(hass, result["flow_id"], {CONF_DEVICE_NAME: "Boiler"})

    await choose(hass, result["flow_id"], "save")

    assert sorted(s.title for s in entry.subentries.values()) == ["Boiler", "Heat pump"]
    assert CONF_ENTITIES in next(iter(entry.subentries.values())).data
