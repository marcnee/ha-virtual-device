"""Which attributes of the source are copied to the virtual entity (pure logic)."""

from custom_components.virtual_device.attributes import attribute_template_error, copied_attributes

SOURCE_ATTRIBUTES = {
    "friendly_name": "Heat pump status",
    "unit_of_measurement": "°C",
    "icon": "mdi:heat-pump",
    "error_code": 7,
    "mode": "eco",
    "last_run": "yesterday",
}


def test_nothing_is_copied_by_default() -> None:
    assert copied_attributes({}, SOURCE_ATTRIBUTES) == {}


def test_none_copies_nothing() -> None:
    assert copied_attributes({"copy_attributes": "none"}, SOURCE_ATTRIBUTES) == {}


def test_all_copies_everything_except_attributes_the_entity_defines_itself() -> None:
    result = copied_attributes({"copy_attributes": "all"}, SOURCE_ATTRIBUTES)

    assert result == {"error_code": 7, "last_run": "yesterday"}


def test_selected_copies_only_the_chosen_attributes() -> None:
    config = {"copy_attributes": "selected", "attribute_names": ["error_code", "missing"]}

    assert copied_attributes(config, SOURCE_ATTRIBUTES) == {"error_code": 7}


def test_reserved_attributes_are_never_copied_even_when_chosen() -> None:
    config = {"copy_attributes": "selected", "attribute_names": ["friendly_name", "icon", "mode"]}

    assert copied_attributes(config, SOURCE_ATTRIBUTES) == {}


def test_without_a_source_state_nothing_is_copied() -> None:
    assert copied_attributes({"copy_attributes": "all"}, None) == {}


def test_valid_attribute_templates_have_no_error() -> None:
    assert attribute_template_error({"fehler": "{{ attributes.error_code }}"}) is None


def test_attribute_templates_must_be_a_mapping() -> None:
    assert attribute_template_error(["{{ value }}"]) == ("attribute_templates_invalid", "")


def test_every_attribute_template_must_be_text() -> None:
    assert attribute_template_error({"fehler": 5}) == ("attribute_templates_invalid", "fehler")
    assert attribute_template_error({"fehler": " "}) == ("attribute_templates_invalid", "fehler")


def test_attribute_names_must_not_be_reserved() -> None:
    assert attribute_template_error({"icon": "{{ value }}"}) == ("attribute_name_reserved", "icon")
    assert attribute_template_error({"source_entity": "x"}) == (
        "attribute_name_reserved",
        "source_entity",
    )
