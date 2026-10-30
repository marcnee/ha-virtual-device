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


def preview(hass: HomeAssistant, state: State | None = SOURCE, **config: Any) -> dict[str, str]:
    return build_preview(hass, {CONF_SOURCE_ENTITY: "sensor.status", **config}, state)


def test_without_a_source_there_is_nothing_to_show(hass: HomeAssistant) -> None:
    assert build_preview(hass, {}, None) == {
        "source_value": NOTHING,
        "value_result": NOTHING,
        "attribute_results": NOTHING,
    }


def test_a_source_that_does_not_exist_shows_nothing(hass: HomeAssistant) -> None:
    assert preview(hass, None)["source_value"] == NOTHING


def test_the_value_of_the_source_is_shown(hass: HomeAssistant) -> None:
    result = preview(hass)

    assert result["source_value"] == "`18 - Running`"
    assert result["value_result"] == NOTHING
    assert result["attribute_results"] == NOTHING


def test_a_source_attribute_is_shown_instead_of_the_state(hass: HomeAssistant) -> None:
    assert preview(hass, **{CONF_SOURCE_ATTRIBUTE: "error_code"})["source_value"] == "`7`"


def test_a_source_without_a_value_shows_nothing(hass: HomeAssistant) -> None:
    assert preview(hass, State("sensor.status", "unknown"))["source_value"] == NOTHING
    assert preview(hass, **{CONF_SOURCE_ATTRIBUTE: "missing"})["source_value"] == NOTHING


def test_the_result_of_the_value_template_is_shown(hass: HomeAssistant) -> None:
    result = preview(hass, **{CONF_VALUE_TEMPLATE: "{{ value.split(' - ')[-1] }}"})

    assert result["value_result"] == "`Running`"


def test_a_value_template_that_gives_no_value_shows_nothing(hass: HomeAssistant) -> None:
    assert preview(hass, **{CONF_VALUE_TEMPLATE: "{{ none }}"})["value_result"] == NOTHING


def test_a_failing_value_template_shows_the_error(hass: HomeAssistant) -> None:
    result = preview(hass, **{CONF_VALUE_TEMPLATE: "{{ value | int(strict=True) }}"})

    assert result["value_result"].startswith("⚠ ")
    assert len(result["value_result"]) > 3


def test_attribute_templates_show_their_results_and_errors(hass: HomeAssistant) -> None:
    templates = {
        "next_code": "{{ attributes.error_code | int + 1 }}",
        "bad": "{{ value | int(strict=True) }}",
    }

    text = preview(hass, **{CONF_ATTRIBUTE_TEMPLATES: templates})["attribute_results"]

    assert "`next_code`: `8`" in text
    assert "`bad`: ⚠ " in text


def test_long_values_are_cut_and_markup_is_made_harmless(hass: HomeAssistant) -> None:
    state = State("sensor.status", "a`b\n" + "x" * 200)

    text = preview(hass, state)["source_value"]

    assert "\n" not in text
    assert text.count("`") == 2
    assert text.endswith("…`")
    assert len(text) < 120
