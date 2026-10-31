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


CODE = "sensor.error_code"


def test_a_value_template_sees_the_extra_sources_by_entity_id(hass: HomeAssistant) -> None:
    hass.states.async_set(CODE, "133 - 133:Flame lost")
    template = "{{ value }} - {{ sources['sensor.error_code'].state.split(':')[-1] }}"
    transform = ValueTransformer(hass, template, "x", [CODE])

    assert transform.render("29.10.2026", STATE) == "29.10.2026 - Flame lost"


def test_the_extra_sources_are_read_when_the_template_is_rendered(hass: HomeAssistant) -> None:
    transform = ValueTransformer(hass, "{{ sources['sensor.error_code'].state }}", "x", [CODE])

    hass.states.async_set(CODE, "1")
    assert transform.render("a", STATE) == "1"
    hass.states.async_set(CODE, "2")
    assert transform.render("a", STATE) == "2"


def test_an_extra_source_that_does_not_exist_makes_the_template_fail(hass: HomeAssistant) -> None:
    transform = ValueTransformer(hass, "{{ sources['sensor.error_code'].state }}", "x", [CODE])

    with pytest.raises(TemplateError):
        transform.render("a", STATE)


def test_without_extra_sources_the_template_sees_none(hass: HomeAssistant) -> None:
    transform = ValueTransformer(hass, "{{ sources | length }}", "x")

    assert transform.render("a", STATE) == "0"


def test_attribute_templates_see_the_extra_sources_too(hass: HomeAssistant) -> None:
    hass.states.async_set(CODE, "133")
    transform = AttributeTransformer(
        hass, {"code": "{{ sources['sensor.error_code'].state | int }}"}, "x", [CODE]
    )

    assert transform.render("a", STATE) == {"code": 133}
