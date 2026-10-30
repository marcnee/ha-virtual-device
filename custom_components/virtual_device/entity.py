"""Base class for all virtual entities."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, EventStateChangedData, State, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_state_change_event

from .actions import ActionRunner
from .attributes import copied_attributes
from .const import (
    ACTION_KEYS,
    ATTR_FORWARDS_COMMANDS,
    ATTR_SOURCE_ATTRIBUTE,
    ATTR_SOURCE_ENTITY,
    CONF_ATTRIBUTE_TEMPLATES,
    CONF_ICON,
    CONF_ID,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_NAME,
    CONF_SOURCE_ATTRIBUTE,
    CONF_SOURCE_ENTITY,
    CONF_VALUE_TEMPLATE,
    DOMAIN,
)
from .transform import AttributeTransformer, ValueTransformer

_LOGGER = logging.getLogger(__name__)


def make_unique_id(subentry_id: str, config_id: str) -> str:
    """The unique ID of a virtual entity."""
    return f"{subentry_id}_{config_id}"


class VirtualEntity(Entity):
    """An entity that belongs to the virtual device and follows a source entity."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, subentry: ConfigSubentry, config: dict[str, Any]) -> None:
        self._config = config
        self._source: str | None = config.get(CONF_SOURCE_ENTITY)
        self._attribute: str | None = config.get(CONF_SOURCE_ATTRIBUTE)
        self._transform: ValueTransformer | None = None
        self._attribute_transform: AttributeTransformer | None = None
        self._actions: dict[str, ActionRunner] = {}
        self._derived: dict[str, Any] = {}
        self._attr_name = config[CONF_NAME]
        self._attr_unique_id = make_unique_id(subentry.subentry_id, config[CONF_ID])
        self._attr_icon = config.get(CONF_ICON)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.title,
            # Always set, so that clearing a value removes it from the device.
            manufacturer=subentry.data.get(CONF_MANUFACTURER),
            model=subentry.data.get(CONF_MODEL),
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Attributes copied from the source, plus the marking of where the entity is wired to."""
        attributes = dict(self._derived)
        if self._source:
            attributes[ATTR_SOURCE_ENTITY] = self._source
        if self._attribute:
            attributes[ATTR_SOURCE_ATTRIBUTE] = self._attribute
        if self._actions:
            attributes[ATTR_FORWARDS_COMMANDS] = True
        return attributes or None

    async def async_added_to_hass(self) -> None:
        """Prepare value transformation and actions, follow the source entity."""
        name = str(self._attr_name)
        self._transform = ValueTransformer(self.hass, self._config.get(CONF_VALUE_TEMPLATE), name)
        self._attribute_transform = AttributeTransformer(
            self.hass, self._config.get(CONF_ATTRIBUTE_TEMPLATES, {}), name
        )
        self._actions = self._build_actions(name)
        if self._source:
            self.async_on_remove(
                async_track_state_change_event(self.hass, [self._source], self._handle_source_event)
            )
            self._refresh()

    def _build_actions(self, name: str) -> dict[str, ActionRunner]:
        """Prepare the configured actions. An invalid one only disables that command."""
        actions: dict[str, ActionRunner] = {}
        for key in ACTION_KEYS:
            if not self._config.get(key):
                continue
            try:
                actions[key] = ActionRunner(self.hass, self._config[key], name)
            except vol.Invalid as err:
                _LOGGER.error("Invalid action (%s) of '%s': %s", key, name, err)
        return actions

    @callback
    def _handle_source_event(self, event: Event[EventStateChangedData]) -> None:
        self._refresh()
        self.async_write_ha_state()

    @callback
    def _refresh(self) -> None:
        """Derive availability and value from the current source state."""
        source_state = self.hass.states.get(self._source)
        self._attr_available = source_state is not None and source_state.state != STATE_UNAVAILABLE
        self._derived = {}
        if source_state is not None:
            self._derived = copied_attributes(self._config, source_state.attributes)
            self._derived |= self._attribute_transform(self._raw_value(source_state), source_state)
        # An icon of its own wins; otherwise the entity looks like its source.
        self._attr_icon = self._config.get(CONF_ICON) or (
            source_state.attributes.get("icon") if source_state else None
        )
        if self._attr_available:
            self._apply(self._transform(self._raw_value(source_state), source_state))

    def _raw_value(self, source_state: State) -> Any | None:
        """The attribute or state of the source; None if it has no value."""
        if self._attribute:
            return source_state.attributes.get(self._attribute)
        return None if source_state.state == STATE_UNKNOWN else source_state.state

    @callback
    def _apply(self, value: Any | None) -> None:
        """Take over the source value (None = unknown). Implemented per platform."""
        raise NotImplementedError

    async def _run_action(self, key: str, **variables: Any) -> None:
        """Forward a command by running the configured action."""
        runner = self._actions.get(key)
        if runner is None:
            raise HomeAssistantError(f"'{self._attr_name}' has no action configured ({key})")
        source_state = self.hass.states.get(self._source) if self._source else None
        context_variables = {"source_entity": self._source, "source_state": source_state}
        await runner.async_run({**context_variables, **variables}, self._context)
