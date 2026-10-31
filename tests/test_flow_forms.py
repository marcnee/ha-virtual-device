"""The schemas of the flow forms."""

import pytest
import voluptuous as vol

from custom_components.virtual_device.const import PLATFORMS
from custom_components.virtual_device.device_classes import (
    BINARY_SENSOR_DEVICE_CLASSES,
    SENSOR_DEVICE_CLASSES,
)
from custom_components.virtual_device.flow_forms import (
    attributes_schema,
    basics_schema,
    details_schema,
    device_schema,
    source_schema,
    suggest,
)


def fields(schema: vol.Schema) -> dict[str, vol.Marker]:
    return {str(key): key for key in schema.schema}


def selector(schema: vol.Schema, name: str):
    return schema.schema[fields(schema)[name]]


def test_suggest_prefills_a_field_from_the_draft() -> None:
    assert suggest({"icon": "mdi:fan"}, "icon") == {"suggested_value": "mdi:fan"}
    assert suggest({}, "icon") == {"suggested_value": None}


@pytest.mark.parametrize(
    ("platform", "names"),
    [
        ("sensor", {"unit_of_measurement", "device_class", "state_class"}),
        ("binary_sensor", {"device_class"}),
        ("switch", {"action_on", "action_off"}),
        ("number", {"min_value", "max_value", "step", "unit_of_measurement", "action_set"}),
        ("select", {"options", "action_select"}),
        ("button", {"action_press"}),
    ],
)
def test_every_type_has_its_own_details(platform: str, names: set[str]) -> None:
    assert set(fields(details_schema(platform, {}))) == names


def test_every_type_has_details() -> None:
    for platform in PLATFORMS:
        assert fields(details_schema(str(platform), {}))


def test_an_unknown_type_has_no_details() -> None:
    with pytest.raises(ValueError, match="Unknown platform"):
        details_schema("light", {})


def test_the_device_classes_follow_the_type() -> None:
    sensor = selector(details_schema("sensor", {}), "device_class")
    binary = selector(details_schema("binary_sensor", {}), "device_class")

    assert sorted(sensor.config["options"]) == SENSOR_DEVICE_CLASSES
    assert sorted(binary.config["options"]) == BINARY_SENSOR_DEVICE_CLASSES
    assert "door" in binary.config["options"]
    assert "door" not in sensor.config["options"]


def defaults(schema: vol.Schema) -> dict[str, object]:
    return {str(key): key.default() for key in schema.schema if key.default is not vol.UNDEFINED}


def test_a_number_has_defaults_for_its_range_unless_the_draft_has_one() -> None:
    assert defaults(details_schema("number", {})) == {"min_value": 0, "max_value": 100, "step": 1}

    draft = {"min_value": 10, "max_value": 30, "step": 0.5}
    assert defaults(details_schema("number", draft)) == draft


def test_the_basics_offer_every_type_and_default_to_a_sensor() -> None:
    schema = basics_schema({})

    assert set(fields(schema)) == {"platform", "name", "icon"}
    assert selector(schema, "platform").config["options"] == [str(p) for p in PLATFORMS]
    assert fields(schema)["platform"].default() == "sensor"


def test_the_basics_start_with_the_draft() -> None:
    schema = basics_schema({"platform": "switch", "name": "Power", "icon": "mdi:power"})

    assert fields(schema)["platform"].default() == "switch"
    assert fields(schema)["name"].default() == "Power"
    assert fields(schema)["icon"].description == {"suggested_value": "mdi:power"}


def test_the_source_form_requires_only_the_source_entity() -> None:
    schema = source_schema({"source_entity": "sensor.x"})

    assert set(fields(schema)) == {
        "source_entity",
        "extra_sources",
        "source_attribute",
        "value_template",
        "copy_attributes",
        "attribute_templates",
        "test_template",
    }
    assert [n for n, key in fields(schema).items() if isinstance(key, vol.Required)] == [
        "source_entity"
    ]
    assert fields(schema)["source_entity"].description == {"suggested_value": "sensor.x"}
    assert fields(schema)["test_template"].default is vol.UNDEFINED  # never prefilled


def test_the_extra_sources_are_chosen_from_all_entities_and_are_optional() -> None:
    schema = source_schema({"extra_sources": ["sensor.a", "sensor.b"]})

    assert selector(schema, "extra_sources").config["multiple"] is True
    assert isinstance(fields(schema)["extra_sources"], vol.Optional)
    assert fields(schema)["extra_sources"].description == {
        "suggested_value": ["sensor.a", "sensor.b"]
    }


def test_the_attribute_choice_offers_the_attributes_of_the_source_and_free_input() -> None:
    schema = attributes_schema({"attribute_names": ["a"]}, ["a", "b"])
    chooser = selector(schema, "attribute_names")

    assert chooser.config["options"] == ["a", "b"]
    assert chooser.config["multiple"] is True
    assert chooser.config["custom_value"] is True
    assert fields(schema)["attribute_names"].description == {"suggested_value": ["a"]}


def test_the_device_form_requires_only_the_name() -> None:
    schema = device_schema({"device_name": "Heat pump", "manufacturer": "ACME"})

    assert set(fields(schema)) == {"device_name", "manufacturer", "model"}
    assert [n for n, key in fields(schema).items() if isinstance(key, vol.Required)] == [
        "device_name"
    ]
    assert fields(schema)["manufacturer"].description == {"suggested_value": "ACME"}
    assert fields(schema)["model"].description == {"suggested_value": None}
