"""Suggested settings derived from a source entity (pure logic, no Home Assistant needed)."""

from typing import Any

import pytest
from homeassistant.core import State

from custom_components.virtual_device.const import (
    CONF_DEVICE_CLASS,
    CONF_MAX,
    CONF_MIN,
    CONF_NAME,
    CONF_OPTIONS,
    CONF_PLATFORM,
    CONF_STATE_CLASS,
    CONF_STEP,
    CONF_UNIT,
)
from custom_components.virtual_device.source_defaults import defaults_from_source


def defaults(entity_id: str, state: str = "1", **attributes: Any) -> dict[str, Any]:
    return defaults_from_source(State(entity_id, state, attributes))


def test_missing_source_gives_no_defaults() -> None:
    assert defaults_from_source(None) == {}


def test_name_is_the_friendly_name() -> None:
    assert defaults("sensor.x", friendly_name="Heat pump status")[CONF_NAME] == "Heat pump status"


def test_name_falls_back_to_the_entity_id() -> None:
    assert defaults("sensor.heatpump_status")[CONF_NAME] == "heatpump status"


@pytest.mark.parametrize(
    ("entity_id", "platform"),
    [
        ("sensor.x", "sensor"),
        ("number.x", "number"),
        ("input_number.x", "number"),
        ("switch.x", "switch"),
        ("input_boolean.x", "switch"),
        ("select.x", "select"),
        ("input_select.x", "select"),
        ("binary_sensor.x", "binary_sensor"),
        ("climate.x", "sensor"),
    ],
)
def test_platform_follows_the_source_domain(entity_id: str, platform: str) -> None:
    assert defaults(entity_id)[CONF_PLATFORM] == platform


def test_unit_and_classes_are_taken_over() -> None:
    result = defaults(
        "sensor.x",
        unit_of_measurement="°C",
        device_class="temperature",
        state_class="measurement",
    )

    assert result[CONF_UNIT] == "°C"
    assert result[CONF_DEVICE_CLASS] == "temperature"
    assert result[CONF_STATE_CLASS] == "measurement"


@pytest.mark.parametrize("device_class", ["enum", "timestamp", "date", "no_such_class"])
def test_device_classes_that_cannot_be_offered_are_skipped(device_class: str) -> None:
    assert CONF_DEVICE_CLASS not in defaults("sensor.x", device_class=device_class)


def test_unknown_state_class_is_skipped() -> None:
    assert CONF_STATE_CLASS not in defaults("sensor.x", state_class="weird")


def test_number_range_is_taken_over() -> None:
    result = defaults("number.x", min=10, max=30, step=0.5)

    assert (result[CONF_MIN], result[CONF_MAX], result[CONF_STEP]) == (10, 30, 0.5)


def test_select_options_are_taken_over() -> None:
    assert defaults("select.x", options=["a", "b"])[CONF_OPTIONS] == ["a", "b"]


def test_attributes_that_are_not_there_give_no_keys() -> None:
    assert set(defaults("sensor.x")) == {CONF_NAME, CONF_PLATFORM}
