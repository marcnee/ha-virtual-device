"""Running the actions that forward commands to the source integration."""

from __future__ import annotations

from typing import Any

from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.script import Script

from .const import DOMAIN


class ActionRunner:
    """A configured sequence of Home Assistant actions (like a script)."""

    def __init__(self, hass: HomeAssistant, actions: list[dict[str, Any]], name: str) -> None:
        self._script = Script(hass, cv.SCRIPT_SCHEMA(actions), name, DOMAIN)

    async def async_run(self, variables: dict[str, Any], context: Context | None) -> None:
        """Run the actions; `variables` are available in their templates."""
        await self._script.async_run(run_variables=variables, context=context)
