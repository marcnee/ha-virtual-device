"""Small helpers shared by the tests."""

from typing import Any

from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    SOURCE_USER,
    ConfigEntry,
    ConfigSubentry,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult, FlowResultType

from custom_components.virtual_device.const import CONF_ENTITIES, SUBENTRY_TYPE_DEVICE


def subentry_by_title(entry: ConfigEntry, title: str) -> ConfigSubentry:
    """The virtual device (subentry) with the given name."""
    return next(s for s in entry.subentries.values() if s.title == title)


def saved_entities(entry: ConfigEntry, title: str = "Heat pump") -> list[dict[str, Any]]:
    """The stored entity definitions of a virtual device."""
    return list(subentry_by_title(entry, title).data[CONF_ENTITIES])


async def reconfigure(
    hass: HomeAssistant, entry: ConfigEntry, title: str = "Heat pump"
) -> FlowResult:
    """Open the flow that edits an existing virtual device."""
    return await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_DEVICE),
        context={
            "source": SOURCE_RECONFIGURE,
            "subentry_id": subentry_by_title(entry, title).subentry_id,
        },
    )


async def new_device(hass: HomeAssistant, entry: ConfigEntry) -> FlowResult:
    """Open the flow that adds a virtual device."""
    return await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_DEVICE), context={"source": SOURCE_USER}
    )


async def choose(hass: HomeAssistant, flow_id: str, step: str) -> FlowResult:
    """Pick a menu entry."""
    return await hass.config_entries.subentries.async_configure(flow_id, {"next_step_id": step})


async def submit(hass: HomeAssistant, flow_id: str, user_input: dict[str, Any]) -> FlowResult:
    """Submit a form."""
    return await hass.config_entries.subentries.async_configure(flow_id, user_input)


def suggested(result: FlowResult) -> dict[str, Any]:
    """Prefilled values of a form (suggested values and defaults), without empty ones."""
    values = {}
    for key in result["data_schema"].schema:
        if key.description and "suggested_value" in key.description:
            values[str(key)] = key.description["suggested_value"]
        elif callable(key.default):
            values[str(key)] = key.default()
    return {k: v for k, v in values.items() if v is not None}


async def source_form(
    hass: HomeAssistant, entry: ConfigEntry, basics: dict[str, Any]
) -> FlowResult:
    """Walk through "add entity" up to the source form."""
    result = await reconfigure(hass, entry)
    result = await choose(hass, result["flow_id"], "add_entity")
    return await submit(hass, result["flow_id"], basics)


async def skip_details(hass: HomeAssistant, result: FlowResult) -> FlowResult:
    """Submit the form with the settings of the entity type without changing anything."""
    assert result["step_id"] == "entity_details"
    return await submit(hass, result["flow_id"], {})


async def save(hass: HomeAssistant, result: FlowResult) -> None:
    """Choose "save" in the menu and check that the device was saved.

    A form with the settings of the entity type that is still open is submitted unchanged first.
    """
    if result["step_id"] == "entity_details":
        result = await skip_details(hass, result)
    result = await choose(hass, result["flow_id"], "save")
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
