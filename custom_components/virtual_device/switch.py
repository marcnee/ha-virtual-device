"""Virtual switches."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ACTION_OFF, CONF_ACTION_ON
from .entity import VirtualEntity
from .manager import VirtualDeviceConfigEntry
from .transform import to_bool


async def async_setup_entry(
    hass: HomeAssistant, entry: VirtualDeviceConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create the virtual switches of a virtual device."""
    await entry.runtime_data.async_register_platform(Platform.SWITCH, VirtualSwitch)


class VirtualSwitch(VirtualEntity, SwitchEntity):
    """A switch whose state follows the source and whose commands run actions."""

    @callback
    def _apply(self, value: Any | None) -> None:
        self._attr_is_on = None if value is None else to_bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Forward the turn-on command."""
        await self._run_action(CONF_ACTION_ON)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Forward the turn-off command."""
        await self._run_action(CONF_ACTION_OFF)
