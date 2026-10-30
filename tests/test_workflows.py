"""The workflow that checks newer Home Assistant versions must stay set up as intended."""

from pathlib import Path

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
