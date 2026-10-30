"""Config flow for Virtual Device."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback

from .const import CONF_DEVICE_NAME, CONF_ENTITIES, DOMAIN
from .options_flow import VirtualDeviceOptionsFlow


class VirtualDeviceConfigFlow(ConfigFlow, domain=DOMAIN):
    """Create a new, initially empty virtual device."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Ask for the device name."""
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_DEVICE_NAME],
                data={CONF_DEVICE_NAME: user_input[CONF_DEVICE_NAME]},
                options={CONF_ENTITIES: []},
            )
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({vol.Required(CONF_DEVICE_NAME): str})
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Manage the entities of the virtual device."""
        return VirtualDeviceOptionsFlow()
