"""Shared fixtures."""

from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from homeassistant.config_entries import ConfigSubentryData
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.virtual_device.const import CONF_ENTITIES, DOMAIN, SUBENTRY_TYPE_DEVICE

SetupDevice = Callable[[list[dict[str, Any]]], Awaitable[MockConfigEntry]]
SetupDevices = Callable[[dict[str, list[dict[str, Any]]]], Awaitable[MockConfigEntry]]


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations):
    """Allow Home Assistant to load custom_components/ in every test."""
    return


@pytest.fixture
def setup_devices(hass: HomeAssistant) -> SetupDevices:
    """Set up the service with one virtual device per name and its entity definitions."""

    async def _setup(devices: dict[str, list[dict[str, Any]]]) -> MockConfigEntry:
        entry = MockConfigEntry(
            domain=DOMAIN,
            version=2,
            data={},
            subentries_data=[
                ConfigSubentryData(
                    data={CONF_ENTITIES: entities},
                    subentry_type=SUBENTRY_TYPE_DEVICE,
                    title=name,
                    unique_id=None,
                )
                for name, entities in devices.items()
            ],
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        return entry

    return _setup


@pytest.fixture
def setup_device(setup_devices: SetupDevices) -> SetupDevice:
    """Set up the service with the single virtual device "Heat pump"."""

    async def _setup(entities: list[dict[str, Any]]) -> MockConfigEntry:
        return await setup_devices({"Heat pump": entities})

    return _setup
