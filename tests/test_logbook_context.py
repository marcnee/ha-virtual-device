"""With the real logbook: the change at the source is "triggered by" the virtual entity."""

from datetime import timedelta

import pytest
from homeassistant.auth.models import User
from homeassistant.components.logbook.helpers import async_determine_event_types
from homeassistant.components.logbook.processor import EventProcessor
from homeassistant.core import Context, HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)

from custom_components.virtual_device.const import (
    CONF_ACTION_ON,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
    EVENT_COMMAND_FORWARDED,
)

from .conftest import SetupDevice

SOURCE = "input_boolean.heatpump"
ENTITY_ID = "switch.heat_pump_power"


@pytest.fixture(autouse=True)
def _enable_custom_integrations():
    """Replaces the shared one: the recorder has to be set up before `hass`, so this module's
    test asks for `enable_custom_integrations` itself, after `recorder_mock`."""


async def test_the_logbook_shows_the_virtual_entity_as_the_cause(
    recorder_mock,
    enable_custom_integrations,
    hass: HomeAssistant,
    setup_device: SetupDevice,
    hass_admin_user: User,
) -> None:
    """With the real logbook: the change at the source is "triggered by" the virtual entity."""
    # The logbook needs the frontend, whose package the test environment lacks.
    hass.config.components.add("frontend")
    assert await async_setup_component(hass, "logbook", {})
    assert await async_setup_component(hass, "input_boolean", {"input_boolean": {"heatpump": {}}})
    source = SOURCE
    await setup_device(
        [
            {
                CONF_ID: "power",
                CONF_PLATFORM: "switch",
                CONF_NAME: "Power",
                CONF_SOURCE_ENTITY: source,
                CONF_ACTION_ON: [
                    {
                        "action": "input_boolean.turn_on",
                        "target": {"entity_id": "{{ source_entity }}"},
                    }
                ],
            }
        ]
    )
    start = dt_util.utcnow()

    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": ENTITY_ID},
        blocking=True,
        context=Context(user_id=hass_admin_user.id),
    )
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)
    entries = await hass.async_add_executor_job(
        EventProcessor(hass, async_determine_event_types(hass, None, None)).get_events,
        start,
        dt_util.utcnow() + timedelta(seconds=1),
    )

    changed = next(e for e in entries if e.get("entity_id") == source and e.get("state") == "on")
    assert changed["context_event_type"] == EVENT_COMMAND_FORWARDED
    assert changed["context_name"] == "Heat pump Power"
    assert changed["context_message"] == f"forwarded the on command to {source}"
    assert changed["context_entity_id"] == ENTITY_ID
    announced = next(e for e in entries if e.get("domain") == "virtual_device")
    assert announced["entity_id"] == ENTITY_ID
    assert announced["context_user_id"] == hass_admin_user.id
