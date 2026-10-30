"""Every step, field and error of the flows needs an English text."""

import json
import re
from pathlib import Path

import pytest

from custom_components.virtual_device.const import COPY_MODES, PLATFORMS

EN_JSON = Path(__file__).parents[1] / "custom_components/virtual_device/translations/en.json"
STRINGS = json.loads(EN_JSON.read_text())

SOURCE_FIELDS = [
    "source_entity",
    "source_attribute",
    "value_template",
    "copy_attributes",
    "attribute_names",
]
OPTION_FIELDS = {
    "add_from_source": SOURCE_FIELDS,
    "add_entity": ["platform", "name", "icon"],
    "entity_source": SOURCE_FIELDS,
    "entity_details": [
        "min_value",
        "max_value",
        "step",
        "unit_of_measurement",
        "device_class",
        "state_class",
        "options",
        "action_on",
        "action_off",
        "action_set",
        "action_select",
        "action_press",
    ],
    "edit_entity": ["virtual_entity"],
    "remove_entity": ["virtual_entity"],
}


DEVICE = STRINGS.get("config_subentries", {}).get("device", {})


def test_service_setup_texts() -> None:
    assert STRINGS["config"]["step"]["user"]["description"]
    assert STRINGS["config"]["abort"]["single_instance_allowed"]


def test_device_flow_entry_texts() -> None:
    assert DEVICE["entry_type"]
    assert DEVICE["initiate_flow"]["user"]
    assert DEVICE["initiate_flow"]["reconfigure"]
    assert DEVICE["abort"]["reconfigure_successful"]
    user = DEVICE["step"]["user"]
    assert user["title"]
    assert user["data"]["device_name"]


def test_device_menu_texts() -> None:
    init = DEVICE["step"]["init"]
    assert init["title"]
    assert set(init["menu_options"]) == {
        "add_from_source",
        "add_entity",
        "edit_entity",
        "remove_entity",
        "save",
    }


@pytest.mark.parametrize(("step", "fields"), OPTION_FIELDS.items())
def test_device_step_texts(step: str, fields: list[str]) -> None:
    texts = DEVICE["step"][step]
    assert texts["title"]
    assert set(fields) <= set(texts["data"])


def test_error_texts() -> None:
    assert {"min_greater_max", "options_required", "attribute_names_required"} <= set(
        DEVICE["error"]
    )


def test_every_platform_has_a_label() -> None:
    labels = STRINGS["selector"]["platform"]["options"]
    assert {str(p) for p in PLATFORMS} <= set(labels)


def _texts(node: object) -> list[str]:
    if isinstance(node, str):
        return [node]
    if isinstance(node, dict):
        return [text for child in node.values() for text in _texts(child)]
    return []


def test_curly_braces_are_escaped_for_the_ui() -> None:
    """The UI formats texts as ICU messages: a literal brace must be written as '{' or '}'."""
    for text in _texts(STRINGS):
        unescaped = re.sub(r"'[{}]+'", "", text)
        assert "{" not in unescaped, text
        assert "}" not in unescaped, text


def test_every_copy_mode_has_a_label() -> None:
    labels = STRINGS["selector"]["copy_attributes"]["options"]
    assert set(COPY_MODES) <= set(labels)
