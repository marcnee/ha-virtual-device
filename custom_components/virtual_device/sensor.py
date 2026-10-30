"""Virtual sensors."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_DEVICE_CLASS, CONF_STATE_CLASS, CONF_UNIT
from .entity import VirtualEntity
from .manager import VirtualDeviceConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: VirtualDeviceConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create the virtual sensors of a virtual device."""
    await entry.runtime_data.async_register_platform(Platform.SENSOR, VirtualSensor)


class VirtualSensor(VirtualEntity, SensorEntity):
    """A sensor showing the (transformed) value of a source entity."""

    def __init__(self, subentry: ConfigSubentry, config: dict[str, Any]) -> None:
        super().__init__(subentry, config)
        self._attr_native_unit_of_measurement = config.get(CONF_UNIT)
        self._attr_device_class = config.get(CONF_DEVICE_CLASS)
        self._attr_state_class = config.get(CONF_STATE_CLASS)
        # Home Assistant requires numbers once a unit or class is set.
        self._numeric = bool(
            self._attr_native_unit_of_measurement
            or self._attr_device_class
            or self._attr_state_class
        )

    @callback
    def _apply(self, value: Any | None) -> None:
        if value is not None and self._numeric and not _is_number(value):
            _LOGGER.warning(
                "Value %r of '%s' is not numeric but a unit or class is configured",
                value,
                self._attr_name,
            )
            value = None
        self._attr_native_value = value


def _is_number(value: Any) -> bool:
    try:
        float(value)
    except TypeError, ValueError:
        return False
    return True
