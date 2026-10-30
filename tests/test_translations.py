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
    "attribute_templates",
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
    "select_attributes": ["attribute_names"],
    "device_settings": ["device_name", "manufacturer", "model"],
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
    assert set(user["data"]) >= {"device_name", "manufacturer", "model"}


def test_device_menu_texts() -> None:
    init = DEVICE["step"]["init"]
    assert init["title"]
    assert set(init["menu_options"]) == {
        "add_from_source",
        "add_entity",
        "edit_entity",
        "remove_entity",
        "device_settings",
        "save",
    }


@pytest.mark.parametrize(("step", "fields"), OPTION_FIELDS.items())
def test_device_step_texts(step: str, fields: list[str]) -> None:
    texts = DEVICE["step"][step]
    assert texts["title"]
    assert set(fields) <= set(texts["data"])


def test_error_texts() -> None:
    assert {
        "min_greater_max",
        "options_required",
        "attribute_names_required",
        "attribute_templates_invalid",
        "attribute_name_reserved",
        "attribute_template_invalid",
    } <= set(DEVICE["error"])


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
    """The UI formats texts as ICU messages: a literal brace must be written as '{' or '}'.

    Only the placeholders the flows fill in ({attribute}, {error}, {device}, {entity},
    {source}) are left as they are.
    """
    for text in _texts(STRINGS):
        unescaped = re.sub(r"'[{}]+'|\{(?:attribute|error|device|entity|source)\}", "", text)
        assert "{" not in unescaped, text
        assert "}" not in unescaped, text


def test_every_copy_mode_has_a_label() -> None:
    labels = STRINGS["selector"]["copy_attributes"]["options"]
    assert set(COPY_MODES) <= set(labels)


ISSUE = STRINGS.get("issues", {}).get("source_missing", {})


def test_source_missing_issue_texts() -> None:
    fix = ISSUE["fix_flow"]
    assert ISSUE["title"]
    assert ISSUE["description"]
    assert fix["step"]["source"]["title"]
    assert fix["step"]["source"]["description"]
    assert fix["step"]["source"]["data"]["source_entity"]
    assert fix["error"]["source_not_found"]
    assert fix["abort"]["entity_not_found"]


def test_source_missing_texts_use_only_the_placeholders_of_the_issue() -> None:
    used = {name for text in _texts(ISSUE) for name in re.findall(r"\{(\w+)\}", text)}
    assert used <= {"device", "entity", "source"}
