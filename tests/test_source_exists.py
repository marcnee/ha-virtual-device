"""A source exists if it has a state or a registry entry."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.virtual_device.source_exists import source_exists


def test_an_entity_with_a_state_exists(hass: HomeAssistant) -> None:
    hass.states.async_set("sensor.a", "1")

    assert source_exists(hass, "sensor.a")


def test_a_disabled_entity_exists_although_it_has_no_state(hass: HomeAssistant) -> None:
    er.async_get(hass).async_get_or_create(
        "sensor",
        "other",
        "b",
        suggested_object_id="b",
        disabled_by=er.RegistryEntryDisabler.USER,
    )

    assert source_exists(hass, "sensor.b")


def test_an_unknown_entity_does_not_exist(hass: HomeAssistant) -> None:
    assert not source_exists(hass, "sensor.nowhere")
