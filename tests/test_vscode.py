"""The VS Code configuration must match the compose services and scripts it refers to."""

import json
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).parents[1]
WORKSPACE = "${workspaceFolder}"


def load_json(name: str) -> dict[str, Any]:
    return json.loads((ROOT / ".vscode" / name).read_text())


LAUNCH = load_json("launch.json")["configurations"]
TASKS = load_json("tasks.json")
COMPOSE = yaml.safe_load((ROOT / "compose.yaml").read_text())["services"]
CHECKS = re.search(r'^ALL="(.*)"$', (ROOT / "scripts/check.sh").read_text(), re.M)[1].split()


def launch(name: str) -> dict[str, Any]:
    return next(config for config in LAUNCH if config["name"] == name)


def attach_configs() -> list[dict[str, Any]]:
    return [config for config in LAUNCH if config["request"] == "attach"]


def test_the_tests_can_be_debugged_locally() -> None:
    assert launch("Tests: all")["module"] == "pytest"
    assert launch("Tests: current file")["args"] == ["${file}"]
    assert all(c["justMyCode"] is False for c in LAUNCH)


def test_both_docker_debug_sessions_exist() -> None:
    assert {c["name"] for c in attach_configs()} == {
        "Attach: tests in Docker",
        "Attach: Home Assistant in Docker",
    }


@pytest.mark.parametrize("config", attach_configs(), ids=lambda c: c["name"])
def test_an_attach_config_matches_the_compose_service_it_connects_to(config) -> None:
    port = config["connect"]["port"]
    services = [s for s in COMPOSE.values() if f"{port}:{port}" in s.get("ports", [])]
    assert len(services) == 1, f"exactly one service must publish port {port}"
    mounts = {volume.split(":")[1]: volume.split(":")[0] for volume in services[0]["volumes"]}
    for mapping in config["pathMappings"]:
        source = "./" + mapping["localRoot"].removeprefix(WORKSPACE).strip("/")
        assert mounts[mapping["remoteRoot"]].rstrip("/.") == source.rstrip("/.")


def test_the_test_debug_service_waits_for_the_debugger() -> None:
    entrypoint = COMPOSE["test-debug"]["entrypoint"]
    assert entrypoint[:3] == ["python", "-m", "debugpy"]
    assert "--wait-for-client" in entrypoint
    assert entrypoint[-2:] == ["-m", "pytest"]
    assert "0.0.0.0:5678" in entrypoint
    assert COMPOSE["test-debug"]["build"]["dockerfile"] == "Dockerfile.test"
    assert "debugpy==" in (ROOT / "requirements_test.txt").read_text()


def test_the_home_assistant_debug_service_runs_the_pinned_version_with_debugpy() -> None:
    service = COMPOSE["homeassistant-debug"]
    dockerfile = (ROOT / service["build"]["dockerfile"]).read_text()
    assert f"FROM {COMPOSE['homeassistant']['image']}" in dockerfile
    assert "debugpy" in dockerfile
    assert service["profiles"] == ["dev"]
    assert service["volumes"] == COMPOSE["homeassistant"]["volumes"]
    assert "0.0.0.0:5679" in service["entrypoint"]


def task_commands() -> list[str]:
    return [task["command"] for task in TASKS["tasks"]]


def test_every_check_has_a_task_and_the_whole_suite_too() -> None:
    commands = task_commands()
    assert "scripts/check.sh" in commands
    for check in CHECKS:
        assert f"scripts/check.sh {check}" in commands


def test_tasks_only_use_compose_services_and_inputs_that_exist() -> None:
    inputs = {i["id"] for i in TASKS["inputs"]}
    for command in task_commands():
        for service in re.findall(
            r"(?:run --rm(?: --service-ports)?|up|restart) ([\w-]+)", command
        ):
            assert service in COMPOSE, command
        for name in re.findall(r"\$\{input:(\w+)\}", command):
            assert name in inputs, command


def test_the_recommended_extensions_include_the_debugger() -> None:
    assert "ms-python.debugpy" in load_json("extensions.json")["recommendations"]


def test_vscode_settings_are_not_ignored_by_git() -> None:
    ignored = (ROOT / ".gitignore").read_text().split()
    assert ".vscode/" not in ignored
