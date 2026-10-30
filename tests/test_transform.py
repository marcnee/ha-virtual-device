"""The pure parts of transforming source values: raw values and rendering that reports errors."""

import pytest
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import TemplateError

from custom_components.virtual_device.transform import (
    AttributeTransformer,
    ValueTransformer,
    raw_value,
)

STATE = State("sensor.x", "18 - Running", {"error_code": 7})


def test_the_raw_value_is_the_state_without_a_source_attribute() -> None:
    assert raw_value(STATE, None) == "18 - Running"


def test_the_raw_value_is_the_source_attribute_if_one_is_configured() -> None:
    assert raw_value(STATE, "error_code") == 7


def test_a_missing_attribute_has_no_raw_value() -> None:
    assert raw_value(STATE, "missing") is None


def test_an_unknown_state_has_no_raw_value() -> None:
    assert raw_value(State("sensor.x", "unknown"), None) is None


def test_rendering_a_value_template_returns_the_result(hass: HomeAssistant) -> None:
    transform = ValueTransformer(hass, "{{ value.split(' - ')[-1] }}", "x")

    assert transform.render("18 - Running", STATE) == "Running"


def test_rendering_reports_a_failing_template_instead_of_hiding_it(hass: HomeAssistant) -> None:
    transform = ValueTransformer(hass, "{{ value | int(strict=True) }}", "x")

    with pytest.raises(TemplateError):
        transform.render("abc", STATE)


def test_calling_the_transformer_still_hides_the_error(hass: HomeAssistant) -> None:
    transform = ValueTransformer(hass, "{{ value | int(strict=True) }}", "x")

    assert transform("abc", STATE) is None


def test_attribute_templates_render_results_and_errors(hass: HomeAssistant) -> None:
    transform = AttributeTransformer(
        hass,
        {"next": "{{ attributes.error_code | int + 1 }}", "bad": "{{ value | int(strict=True) }}"},
        "x",
    )

    rendered = transform.render("abc", STATE)

    assert rendered["next"] == 8
    assert isinstance(rendered["bad"], TemplateError)


def test_calling_the_attribute_transformer_leaves_failing_attributes_out(
    hass: HomeAssistant,
) -> None:
    transform = AttributeTransformer(
        hass,
        {"next": "{{ attributes.error_code | int + 1 }}", "bad": "{{ value | int(strict=True) }}"},
        "x",
    )

    assert transform("abc", STATE) == {"next": 8}
