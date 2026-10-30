"""Virtual numbers."""

from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ACTION_SET, CONF_MAX, CONF_MIN, CONF_STEP, CONF_UNIT
from .entity import VirtualEntity, add_platform_entities


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create the virtual numbers of a virtual device."""
    add_platform_entities(entry, Platform.NUMBER, VirtualNumber, async_add_entities)


class VirtualNumber(VirtualEntity, NumberEntity):
    """A number that follows the source; new values run an action with `value`."""

    def __init__(self, subentry: ConfigSubentry, config: dict[str, Any]) -> None:
        super().__init__(subentry, config)
        self._attr_native_min_value = config.get(CONF_MIN, 0)
        self._attr_native_max_value = config.get(CONF_MAX, 100)
        self._attr_native_step = config.get(CONF_STEP, 1)
        self._attr_native_unit_of_measurement = config.get(CONF_UNIT)

    @callback
    def _apply(self, value: Any | None) -> None:
        try:
            self._attr_native_value = None if value is None else float(value)
        except ValueError:
            self._attr_native_value = None

    async def async_set_native_value(self, value: float) -> None:
        """Forward the new value."""
        await self._run_action(CONF_ACTION_SET, value=value)
