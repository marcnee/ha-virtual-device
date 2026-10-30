"""Shared fixtures."""

from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.virtual_device.const import CONF_DEVICE_NAME, CONF_ENTITIES, DOMAIN

SetupDevice = Callable[[list[dict[str, Any]]], Awaitable[MockConfigEntry]]


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations):
    """Allow Home Assistant to load custom_components/ in every test."""
    return


@pytest.fixture
def setup_device(hass: HomeAssistant) -> SetupDevice:
    """Set up the virtual device "Heat pump" with the given entity configs."""

    async def _setup(entities: list[dict[str, Any]]) -> MockConfigEntry:
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_DEVICE_NAME: "Heat pump"},
            options={CONF_ENTITIES: entities},
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        return entry

    return _setup
