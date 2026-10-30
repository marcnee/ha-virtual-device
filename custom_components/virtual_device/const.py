"""Constants for Virtual Device."""

from homeassistant.const import Platform

DOMAIN = "virtual_device"

# One config entry (the service) holds one subentry of this type per virtual device.
SUBENTRY_TYPE_DEVICE = "device"

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.BUTTON,
]

# Config entry
CONF_DEVICE_NAME = "device_name"
CONF_ENTITIES = "entities"

# Options flow
CONF_PICK = "virtual_entity"

# Keys of one virtual entity definition (stored in the config entry options)
CONF_ID = "id"
CONF_PLATFORM = "platform"
CONF_NAME = "name"
CONF_SOURCE_ENTITY = "source_entity"
CONF_SOURCE_ATTRIBUTE = "source_attribute"
CONF_VALUE_TEMPLATE = "value_template"
CONF_UNIT = "unit_of_measurement"
CONF_MIN = "min_value"
CONF_MAX = "max_value"
CONF_STEP = "step"
CONF_OPTIONS = "options"

# Actions forwarding commands to the source integration
CONF_ACTION_ON = "action_on"
CONF_ACTION_OFF = "action_off"
CONF_ACTION_SET = "action_set"
CONF_ACTION_SELECT = "action_select"
CONF_ACTION_PRESS = "action_press"

ACTION_KEYS = (
    CONF_ACTION_ON,
    CONF_ACTION_OFF,
    CONF_ACTION_SET,
    CONF_ACTION_SELECT,
    CONF_ACTION_PRESS,
)

CONF_DEVICE_CLASS = "device_class"
CONF_STATE_CLASS = "state_class"

CONF_ICON = "icon"

# Which attributes of the source are copied to the virtual entity
CONF_COPY_ATTRIBUTES = "copy_attributes"
CONF_ATTRIBUTE_NAMES = "attribute_names"
COPY_NONE = "none"
COPY_ALL = "all"
COPY_SELECTED = "selected"
COPY_MODES = (COPY_NONE, COPY_ALL, COPY_SELECTED)

# Attributes marking where a virtual entity is wired to.
ATTR_SOURCE_ENTITY = "source_entity"
ATTR_SOURCE_ATTRIBUTE = "source_attribute"
ATTR_FORWARDS_COMMANDS = "forwards_commands"
