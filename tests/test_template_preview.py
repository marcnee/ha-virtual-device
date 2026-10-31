"""The preview of the templates of an entity with the current state of its source."""

from typing import Any

from homeassistant.core import HomeAssistant, State

from custom_components.virtual_device.const import (
    CONF_ATTRIBUTE_TEMPLATES,
    CONF_SOURCE_ATTRIBUTE,
    CONF_SOURCE_ENTITY,
    CONF_VALUE_TEMPLATE,
)
from custom_components.virtual_device.template_preview import NOTHING, build_preview

SOURCE = State("sensor.status", "18 - Running", {"error_code": 7, "name": "Pump"})
VALUE = "Value of the source: "
RESULT = "Result of the value template: "
ATTRIBUTES = "Attribute templates: "


def preview(hass: HomeAssistant, state: State | None = SOURCE, **config: Any) -> str:
    return build_preview(hass, {CONF_SOURCE_ENTITY: "sensor.status", **config}, state)


def test_without_a_source_there_is_no_preview(hass: HomeAssistant) -> None:
    assert build_preview(hass, {}, None) == ""
    assert build_preview(hass, {CONF_VALUE_TEMPLATE: "{{ value }}"}, None) == ""


def test_a_source_that_does_not_exist_shows_nothing_as_its_value(hass: HomeAssistant) -> None:
    assert VALUE + NOTHING in preview(hass, None)


def test_the_value_of_the_source_is_shown(hass: HomeAssistant) -> None:
    assert VALUE + "`18 - Running`" in preview(hass)


def test_only_what_is_configured_is_shown(hass: HomeAssistant) -> None:
    text = preview(hass)

    assert RESULT not in text
    assert ATTRIBUTES not in text


def test_a_source_attribute_is_shown_instead_of_the_state(hass: HomeAssistant) -> None:
    assert VALUE + "`7`" in preview(hass, **{CONF_SOURCE_ATTRIBUTE: "error_code"})


def test_a_source_without_a_value_shows_nothing(hass: HomeAssistant) -> None:
    assert VALUE + NOTHING in preview(hass, State("sensor.status", "unknown"))
    assert VALUE + NOTHING in preview(hass, **{CONF_SOURCE_ATTRIBUTE: "missing"})


def test_the_result_of_the_value_template_is_shown(hass: HomeAssistant) -> None:
    text = preview(hass, **{CONF_VALUE_TEMPLATE: "{{ value.split(' - ')[-1] }}"})

    assert RESULT + "`Running`" in text


def test_a_value_template_that_gives_no_value_shows_nothing(hass: HomeAssistant) -> None:
    assert RESULT + NOTHING in preview(hass, **{CONF_VALUE_TEMPLATE: "{{ none }}"})


def test_a_failing_value_template_shows_the_error(hass: HomeAssistant) -> None:
    text = preview(hass, **{CONF_VALUE_TEMPLATE: "{{ value | int(strict=True) }}"})

    assert RESULT + "⚠ " in text


def test_attribute_templates_show_their_results_and_errors(hass: HomeAssistant) -> None:
    templates = {
        "next_code": "{{ attributes.error_code | int + 1 }}",
        "bad": "{{ value | int(strict=True) }}",
    }

    text = preview(hass, **{CONF_ATTRIBUTE_TEMPLATES: templates})

    assert ATTRIBUTES in text
    assert "`next_code`: `8`" in text
    assert "`bad`: ⚠ " in text


def test_long_values_are_cut_and_markup_is_made_harmless(hass: HomeAssistant) -> None:
    state = State("sensor.status", "a`b\n" + "x" * 200)

    line = next(line for line in preview(hass, state).splitlines() if VALUE in line)

    assert line.count("`") == 2
    assert line.endswith("…`")
    assert len(line) < 120


def test_invalid_attribute_templates_are_ignored(hass: HomeAssistant) -> None:
    """The preview is also built from input that did not pass the checks of the form."""
    for templates in ("text", ["a"], {"": "{{ 1 }}"}, {"a": None}, {"a": " "}, {1: "{{ 1 }}"}):
        assert ATTRIBUTES not in preview(hass, **{CONF_ATTRIBUTE_TEMPLATES: templates})
