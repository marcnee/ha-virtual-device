"""Virtual buttons."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ACTION_PRESS
from .entity import VirtualEntity, add_platform_entities


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create the virtual buttons of a virtual device."""
    add_platform_entities(entry, Platform.BUTTON, VirtualButton, async_add_entities)


class VirtualButton(VirtualEntity, ButtonEntity):
    """A button that runs an action when pressed. It needs no source entity."""

    async def async_press(self) -> None:
        """Forward the press."""
        await self._run_action(CONF_ACTION_PRESS)
