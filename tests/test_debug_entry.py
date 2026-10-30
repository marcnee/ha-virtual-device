"""scripts/debug_entry.py starts a module under debugpy and says when the debugger listens."""

import runpy
import sys
import types

import pytest

from scripts.debug_entry import main, parse_args


def test_the_arguments_are_port_wait_flag_module_and_its_arguments() -> None:
    assert parse_args(["5678", "--wait", "pytest", "-k", "sensor"]) == (
        5678,
        True,
        "pytest",
        ["-k", "sensor"],
    )
    assert parse_args(["5679", "homeassistant", "--config", "/config"]) == (
        5679,
        False,
        "homeassistant",
        ["--config", "/config"],
    )


@pytest.fixture
def steps(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> list:
    """Replace debugpy and runpy; record what happens in which order."""
    steps: list = []

    def listen(address: tuple[str, int]) -> None:
        steps.append(("listen", address))

    def wait_for_client() -> None:
        # The marker must already be out when we start to wait for the debugger.
        steps.append(("wait", capsys.readouterr().out))

    def run_module(module: str, **kwargs: object) -> None:
        steps.append(("run", module, list(sys.argv), kwargs["run_name"]))

    monkeypatch.setitem(
        sys.modules,
        "debugpy",
        types.SimpleNamespace(listen=listen, wait_for_client=wait_for_client),
    )
    monkeypatch.setattr(runpy, "run_module", run_module)
    monkeypatch.setattr(sys, "argv", list(sys.argv))
    return steps


def test_it_listens_says_so_waits_for_the_debugger_and_runs_the_module(steps: list) -> None:
    main(["5678", "--wait", "pytest", "-k", "sensor"])

    assert steps == [
        ("listen", ("0.0.0.0", 5678)),
        ("wait", "Debugger listening on port 5678\n"),
        ("run", "pytest", ["pytest", "-k", "sensor"], "__main__"),
    ]


def test_without_the_wait_flag_the_module_starts_right_away(
    steps: list, capsys: pytest.CaptureFixture[str]
) -> None:
    main(["5679", "homeassistant", "--config", "/config"])

    assert [step[0] for step in steps] == ["listen", "run"]
    assert steps[1][2] == ["homeassistant", "--config", "/config"]
    assert capsys.readouterr().out == "Debugger listening on port 5679\n"
