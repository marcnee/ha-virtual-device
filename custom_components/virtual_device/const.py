"""Constants for Virtual Device."""

from homeassistant.const import Platform

DOMAIN = "virtual_device"

CONF_DEVICE_NAME = "device_name"
CONF_ENTITIES = "entities"

# Keys of one virtual entity definition (stored in the config entry options)
CONF_ID = "id"
CONF_PLATFORM = "platform"
CONF_NAME = "name"
CONF_SOURCE_ENTITY = "source_entity"

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]
CONF_SOURCE_ATTRIBUTE = "source_attribute"
CONF_VALUE_TEMPLATE = "value_template"
