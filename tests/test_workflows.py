"""The workflow that checks newer Home Assistant versions must stay set up as intended."""

from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]
COMPAT = (ROOT / ".github/workflows/ha-compat.yaml").read_text()
DEPENDABOT = (ROOT / ".github/dependabot.yml").read_text()


def test_compat_runs_on_a_schedule_and_on_demand() -> None:
    assert "schedule:" in COMPAT
    assert "workflow_dispatch:" in COMPAT


def test_compat_tests_the_newest_home_assistant_instead_of_the_pinned_one() -> None:
    assert "pip install pytest-homeassistant-custom-component" in COMPAT
    assert "pip install -r requirements_test.txt" not in COMPAT


def test_compat_also_tries_the_beta_but_does_not_fail_the_build_for_it() -> None:
    assert "--pre pytest-homeassistant-custom-component" in COMPAT
    assert "continue-on-error: true" in COMPAT


def test_dependabot_keeps_the_github_actions_up_to_date() -> None:
    assert "package-ecosystem: github-actions" in DEPENDABOT


COMPOSE = yaml.safe_load((ROOT / "compose.yaml").read_text())["services"]
COMPAT_DOCKERFILE = (ROOT / "Dockerfile.compat").read_text()


def test_compose_can_run_the_tests_against_the_newest_release_and_the_beta() -> None:
    assert COMPOSE["test-latest"]["build"]["dockerfile"] == "Dockerfile.compat"
    assert COMPOSE["test-beta"]["build"]["dockerfile"] == "Dockerfile.compat"
    assert COMPOSE["test-beta"]["build"]["args"] == {"PRE": "--pre"}
    assert "args" not in COMPOSE["test-latest"]["build"]


def test_the_compat_image_installs_the_unpinned_package() -> None:
    assert "pip install --no-cache-dir $PRE pytest-homeassistant-custom-component" in (
        COMPAT_DOCKERFILE
    )
    assert "requirements_test.txt" not in COMPAT_DOCKERFILE
