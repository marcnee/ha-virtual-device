"""scripts/check.sh runs every check and reports them all, with a fake docker."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts/check.sh"

FAKE_DOCKER = """#!/bin/sh
echo "$*" >> "$FAKE_DOCKER_LOG"
[ "$*" = "$FAKE_DOCKER_FAIL" ] && exit 1
exit 0
"""


@pytest.fixture
def run_check(tmp_path: Path):
    """Run the script with a docker that only records its calls; returns (result, calls)."""
    (tmp_path / "docker").write_text(FAKE_DOCKER)
    (tmp_path / "docker").chmod(0o755)
    log = tmp_path / "calls.log"

    def run(*steps: str, fail: str = "") -> tuple[subprocess.CompletedProcess[str], list[str]]:
        env = {
            **os.environ,
            "PATH": f"{tmp_path}:{os.environ['PATH']}",
            "FAKE_DOCKER_LOG": str(log),
            "FAKE_DOCKER_FAIL": fail,
        }
        result = subprocess.run(
            ["sh", str(SCRIPT), *steps], capture_output=True, text=True, env=env, check=False
        )
        calls = log.read_text().splitlines() if log.exists() else []
        return result, calls

    return run


def test_everything_runs_in_order(run_check) -> None:
    result, calls = run_check()

    assert result.returncode == 0
    assert calls == [
        "compose run --rm lint",
        "compose run --rm test",
        "compose run --rm hassfest",
        "compose run --rm test-latest",
        "compose run --rm test-beta",
    ]


def test_a_failing_check_does_not_stop_the_others_but_fails_the_run(run_check) -> None:
    result, calls = run_check(fail="compose run --rm test")

    assert result.returncode == 1
    assert len(calls) == 5
    assert "test            FAILED" in result.stdout
    assert "lint            ok" in result.stdout


def test_the_beta_is_informational(run_check) -> None:
    result, _ = run_check(fail="compose run --rm test-beta")

    assert result.returncode == 0
    assert "test-beta       FAILED (informational)" in result.stdout


def test_single_checks_can_be_chosen(run_check) -> None:
    result, calls = run_check("lint", "test")

    assert result.returncode == 0
    assert calls == ["compose run --rm lint", "compose run --rm test"]


def test_an_unknown_check_is_refused(run_check) -> None:
    result, calls = run_check("nonsense")

    assert result.returncode == 2
    assert "nonsense" in result.stderr
    assert calls == []
