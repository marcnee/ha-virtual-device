"""The repair flow lets the user pick a new source for a virtual entity."""

from typing import Any

import pytest
from homeassistant.components.repairs import repairs_flow_manager
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult, FlowResultType
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component

from custom_components.virtual_device.const import (
    CONF_ENTITIES,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
    CONF_VALUE_TEMPLATE,
    DOMAIN,
)
from custom_components.virtual_device.source_issues import issue_id

from .conftest import SetupDevice
from .helpers import saved_entities, subentry_by_title

OLD = "sensor.old_temperature"
NEW = "sensor.new_temperature"


def sensor(config_id: str, source: str = OLD, **extra: Any) -> dict[str, Any]:
    return {
        CONF_ID: config_id,
        CONF_PLATFORM: "sensor",
        CONF_NAME: config_id.title(),
        CONF_SOURCE_ENTITY: source,
        **extra,
    }


@pytest.fixture(autouse=True)
async def _repairs(hass: HomeAssistant) -> None:
    assert await async_setup_component(hass, "repairs", {})


async def start_fix(hass: HomeAssistant, entry, config_id: str = "status") -> FlowResult:
    subentry_id = subentry_by_title(entry, "Heat pump").subentry_id
    return await repairs_flow_manager(hass).async_init(
        DOMAIN, context={"issue_id": issue_id((subentry_id, config_id))}
    )


async def test_the_flow_asks_for_a_new_source(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([sensor("status")])

    result = await start_fix(hass, entry)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "source"
    assert result["description_placeholders"] == {
        "device": "Heat pump",
        "entity": "Status",
        "source": OLD,
    }
    assert list(result["data_schema"].schema) == [CONF_SOURCE_ENTITY]


async def test_the_chosen_source_replaces_the_old_one_and_the_issue_is_resolved(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([sensor("status", **{CONF_VALUE_TEMPLATE: "{{ value | float }}"})])
    hass.states.async_set(NEW, "21.5")
    result = await start_fix(hass, entry)

    result = await repairs_flow_manager(hass).async_configure(
        result["flow_id"], {CONF_SOURCE_ENTITY: NEW}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    [stored] = saved_entities(entry)
    assert stored[CONF_SOURCE_ENTITY] == NEW
    assert stored[CONF_VALUE_TEMPLATE] == "{{ value | float }}"
    assert hass.states.get("sensor.heat_pump_status").state == "21.5"
    assert ir.async_get(hass).issues == {}


async def test_only_the_chosen_entity_changes(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([sensor("status"), sensor("other")])
    hass.states.async_set(NEW, "1")
    result = await start_fix(hass, entry)

    await repairs_flow_manager(hass).async_configure(result["flow_id"], {CONF_SOURCE_ENTITY: NEW})
    await hass.async_block_till_done()

    sources = {e[CONF_ID]: e[CONF_SOURCE_ENTITY] for e in saved_entities(entry)}
    assert sources == {"status": NEW, "other": OLD}


async def test_a_source_that_does_not_exist_is_refused(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([sensor("status")])
    result = await start_fix(hass, entry)

    result = await repairs_flow_manager(hass).async_configure(
        result["flow_id"], {CONF_SOURCE_ENTITY: "sensor.nowhere"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_SOURCE_ENTITY: "source_not_found"}
    assert saved_entities(entry)[0][CONF_SOURCE_ENTITY] == OLD


async def test_the_flow_aborts_when_the_entity_has_been_removed_meanwhile(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([sensor("status")])
    result = await start_fix(hass, entry)
    hass.config_entries.async_update_subentry(
        entry, subentry_by_title(entry, "Heat pump"), data={CONF_ENTITIES: []}
    )
    await hass.async_block_till_done()

    result = await repairs_flow_manager(hass).async_configure(
        result["flow_id"], {CONF_SOURCE_ENTITY: NEW}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "entity_not_found"
