"""Device and state classes a virtual sensor can use."""

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

# Sensors with a device class need numbers, so classes for dates and enums are not offered.
_NON_NUMERIC = {SensorDeviceClass.DATE, SensorDeviceClass.TIMESTAMP, SensorDeviceClass.ENUM}

SENSOR_DEVICE_CLASSES = sorted(c.value for c in SensorDeviceClass if c not in _NON_NUMERIC)
SENSOR_STATE_CLASSES = [c.value for c in SensorStateClass]
