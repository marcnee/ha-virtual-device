"""Virtual selects."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ACTION_SELECT, CONF_OPTIONS
from .entity import VirtualEntity, add_platform_entities


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create the virtual selects of a virtual device."""
    add_platform_entities(entry, Platform.SELECT, VirtualSelect, async_add_entities)


class VirtualSelect(VirtualEntity, SelectEntity):
    """A select that follows the source; the chosen option runs an action with `option`."""

    def __init__(self, subentry: ConfigSubentry, config: dict[str, Any]) -> None:
        super().__init__(subentry, config)
        self._attr_options = list(config[CONF_OPTIONS])

    @callback
    def _apply(self, value: Any | None) -> None:
        option = None if value is None else str(value)
        self._attr_current_option = option if option in self._attr_options else None

    async def async_select_option(self, option: str) -> None:
        """Forward the chosen option."""
        await self._run_action(CONF_ACTION_SELECT, option=option)
