"""Name, manufacturer and model of a virtual device: when creating it and afterwards."""

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.virtual_device.const import (
    CONF_DEVICE_NAME,
    CONF_ENTITIES,
    CONF_MANUFACTURER,
    CONF_MODEL,
)

from .conftest import SetupDevice, SetupDevices
from .helpers import choose, new_device, reconfigure, save, subentry_by_title, submit, suggested

ENTITY = {"id": "a", "platform": "button", "name": "Go"}


async def test_a_new_device_can_get_manufacturer_and_model(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    entry = await setup_devices({})
    result = await new_device(hass, entry)

    result = await submit(
        hass,
        result["flow_id"],
        {CONF_DEVICE_NAME: "Boiler", CONF_MANUFACTURER: "Viessmann", CONF_MODEL: "V1"},
    )
    result = await choose(hass, result["flow_id"], "save")

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Boiler"
    assert result["data"] == {CONF_ENTITIES: [], CONF_MANUFACTURER: "Viessmann", CONF_MODEL: "V1"}


async def test_empty_manufacturer_and_model_are_not_stored(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    entry = await setup_devices({})
    result = await new_device(hass, entry)

    result = await submit(hass, result["flow_id"], {CONF_DEVICE_NAME: "Boiler", CONF_MODEL: ""})
    result = await choose(hass, result["flow_id"], "save")

    assert result["data"] == {CONF_ENTITIES: []}


async def test_device_settings_show_the_current_values(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    entry = await setup_devices({"Heat pump": []})
    subentry = subentry_by_title(entry, "Heat pump")
    hass.config_entries.async_update_subentry(
        entry, subentry, data={CONF_ENTITIES: [], CONF_MANUFACTURER: "Viessmann"}
    )
    result = await reconfigure(hass, entry)

    result = await choose(hass, result["flow_id"], "device_settings")

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "device_settings"
    assert suggested(result) == {CONF_DEVICE_NAME: "Heat pump", CONF_MANUFACTURER: "Viessmann"}


async def test_device_settings_are_saved_together_with_the_entities(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([ENTITY])
    result = await reconfigure(hass, entry)
    result = await choose(hass, result["flow_id"], "device_settings")

    result = await submit(
        hass,
        result["flow_id"],
        {CONF_DEVICE_NAME: "Heater", CONF_MANUFACTURER: "Viessmann", CONF_MODEL: "V1"},
    )
    assert result["type"] is FlowResultType.MENU
    await save(hass, result)

    subentry = next(iter(entry.subentries.values()))
    assert subentry.title == "Heater"
    assert subentry.data == {
        CONF_ENTITIES: [ENTITY],
        CONF_MANUFACTURER: "Viessmann",
        CONF_MODEL: "V1",
    }


async def test_a_cleared_value_is_removed(hass: HomeAssistant, setup_devices: SetupDevices) -> None:
    entry = await setup_devices({"Heat pump": []})
    hass.config_entries.async_update_subentry(
        entry,
        subentry_by_title(entry, "Heat pump"),
        data={CONF_ENTITIES: [], CONF_MANUFACTURER: "Viessmann", CONF_MODEL: "V1"},
    )
    result = await reconfigure(hass, entry)
    result = await choose(hass, result["flow_id"], "device_settings")

    result = await submit(
        hass, result["flow_id"], {CONF_DEVICE_NAME: "Heat pump", CONF_MODEL: "V1"}
    )
    await save(hass, result)

    assert next(iter(entry.subentries.values())).data == {CONF_ENTITIES: [], CONF_MODEL: "V1"}


async def test_nothing_is_saved_before_save_is_chosen(
    hass: HomeAssistant, setup_devices: SetupDevices
) -> None:
    entry = await setup_devices({"Heat pump": []})
    result = await reconfigure(hass, entry)
    result = await choose(hass, result["flow_id"], "device_settings")

    await submit(hass, result["flow_id"], {CONF_DEVICE_NAME: "Heater", CONF_MODEL: "V1"})

    subentry = next(iter(entry.subentries.values()))
    assert subentry.title == "Heat pump"
    assert CONF_MODEL not in subentry.data
