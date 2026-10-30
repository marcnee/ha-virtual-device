"""Checks of what the user entered in the flow forms."""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.virtual_device.const import (
    CONF_ATTRIBUTE_TEMPLATES,
    CONF_MAX,
    CONF_MIN,
    CONF_OPTIONS,
)
from custom_components.virtual_device.flow_validation import validate_details, validate_source


@pytest.mark.parametrize(("minimum", "maximum"), [(10, 10), (30, 10)])
def test_a_number_needs_a_minimum_below_its_maximum(minimum: int, maximum: int) -> None:
    errors = validate_details("number", {CONF_MIN: minimum, CONF_MAX: maximum})

    assert errors == {CONF_MAX: "min_greater_max"}


def test_a_number_with_a_valid_range_has_no_errors() -> None:
    assert validate_details("number", {CONF_MIN: 10, CONF_MAX: 30}) == {}


@pytest.mark.parametrize("user_input", [{}, {CONF_OPTIONS: []}])
def test_a_select_needs_options(user_input: dict) -> None:
    assert validate_details("select", user_input) == {CONF_OPTIONS: "options_required"}


def test_a_select_with_options_has_no_errors() -> None:
    assert validate_details("select", {CONF_OPTIONS: ["On", "Off"]}) == {}


@pytest.mark.parametrize("platform", ["sensor", "binary_sensor", "switch", "button"])
def test_other_types_have_nothing_to_check(platform: str) -> None:
    assert validate_details(platform, {}) == {}


@pytest.mark.parametrize("user_input", [{}, {CONF_ATTRIBUTE_TEMPLATES: {}}])
def test_a_source_without_attribute_templates_is_fine(
    hass: HomeAssistant, user_input: dict
) -> None:
    assert validate_source(hass, user_input) == ({}, {})


def test_valid_attribute_templates_are_fine(hass: HomeAssistant) -> None:
    templates = {"next": "{{ attributes.code | int + 1 }}"}

    assert validate_source(hass, {CONF_ATTRIBUTE_TEMPLATES: templates}) == ({}, {})


def test_a_reserved_attribute_name_is_refused(hass: HomeAssistant) -> None:
    errors, placeholders = validate_source(hass, {CONF_ATTRIBUTE_TEMPLATES: {"icon": "{{ 1 }}"}})

    assert errors == {CONF_ATTRIBUTE_TEMPLATES: "attribute_name_reserved"}
    assert placeholders == {"attribute": "icon"}


def test_an_empty_template_is_refused(hass: HomeAssistant) -> None:
    errors, placeholders = validate_source(hass, {CONF_ATTRIBUTE_TEMPLATES: {"next": " "}})

    assert errors == {CONF_ATTRIBUTE_TEMPLATES: "attribute_templates_invalid"}
    assert placeholders == {"attribute": "next"}


def test_a_template_with_a_syntax_error_names_the_attribute_and_the_error(
    hass: HomeAssistant,
) -> None:
    errors, placeholders = validate_source(hass, {CONF_ATTRIBUTE_TEMPLATES: {"next": "{{ 1 + }}"}})

    assert errors == {CONF_ATTRIBUTE_TEMPLATES: "attribute_template_invalid"}
    assert placeholders["attribute"] == "next"
    assert placeholders["error"]
