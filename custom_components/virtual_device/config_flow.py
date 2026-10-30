"""Config flow for Virtual Device: one service, the devices are config subentries."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
)
from homeassistant.core import callback

from .const import DOMAIN, SUBENTRY_TYPE_DEVICE
from .device_flow import VirtualDeviceSubentryFlow


class VirtualDeviceConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up the service. Virtual devices are added to it afterwards."""

    VERSION = 2

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Confirm the setup of the (single) service."""
        if user_input is not None:
            return self.async_create_entry(title="Virtual Device", data={})
        return self.async_show_form(step_id="user")

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Virtual devices are subentries of the service."""
        return {SUBENTRY_TYPE_DEVICE: VirtualDeviceSubentryFlow}
