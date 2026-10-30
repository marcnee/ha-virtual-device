"""The dev instance starts with demo entities that can serve as sources."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.virtual_device.const import PLATFORMS

ROOT = Path(__file__).parents[1]
CONFIG_FILE = ROOT / "dev-config/configuration.yaml"
NOT_LOADED_IN_TESTS = {"default_config", "logger"}


@pytest.fixture
def expected_lingering_timers() -> bool:
    """The demo entities poll; their timers are not what these tests are about."""
    return True


@pytest.fixture
async def dev_config(hass: HomeAssistant) -> None:
    """Set up everything of the dev configuration that does not need the network."""
    config = {
        domain: value or {}
        for domain, value in yaml.safe_load(CONFIG_FILE.read_text()).items()
        if domain not in NOT_LOADED_IN_TESTS
    }
    # The demo depends on the voice assistant, which the entities do not need (and the test
    # environment lacks its packages).
    hass.config.components.add("conversation")
    # Only the demo platforms that can be sources: the test environment lacks the packages of
    # the others, and the ones without a config entry (geo location, tts, ...) only add timers.
    with (
        patch("homeassistant.components.demo.COMPONENTS_WITH_DEMO_PLATFORM", []),
        patch(
            "homeassistant.components.demo.COMPONENTS_WITH_CONFIG_ENTRY_DEMO_PLATFORM",
            [Platform(platform) for platform in PLATFORMS],
        ),
    ):
        for domain in list(config):
            assert await async_setup_component(hass, domain, config)
        await hass.async_block_till_done()


@pytest.mark.parametrize("platform", PLATFORMS)
@pytest.mark.usefixtures("dev_config")
async def test_every_supported_source_type_has_a_demo_entity(
    hass: HomeAssistant, platform: str
) -> None:
    assert hass.states.async_entity_ids(platform)


@pytest.mark.usefixtures("dev_config")
async def test_a_demo_sensor_has_attributes_to_copy(hass: HomeAssistant) -> None:
    state = hass.states.get("sensor.dev_temperature")

    assert state is not None
    assert state.attributes["room"] == "Living room"
    assert state.attributes["unit_of_measurement"] == "°C"


@pytest.mark.usefixtures("dev_config")
async def test_the_controllable_helpers_exist(hass: HomeAssistant) -> None:
    for entity_id in (
        "input_boolean.notify",
        "input_number.noise_allowance",
        "input_select.who_cooks",
        "input_button.bell",
        "binary_sensor.dev_door",
    ):
        assert hass.states.get(entity_id) is not None, entity_id


def test_helpers_are_left_to_the_demo() -> None:
    """The demo sets these up itself; whichever is set up first would win, so we do not."""
    config = yaml.safe_load(CONFIG_FILE.read_text())
    assert not {"input_boolean", "input_number", "input_select", "input_button"} & config.keys()


def test_both_dev_instances_load_the_dev_configuration() -> None:
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text())["services"]
    mount = "./dev-config/configuration.yaml:/config/configuration.yaml:ro"
    for service in ("homeassistant", "homeassistant-debug"):
        assert mount in compose[service]["volumes"]


def test_the_dev_instance_logs_the_integration_in_detail() -> None:
    config = yaml.safe_load(CONFIG_FILE.read_text())
    assert config["logger"]["logs"]["custom_components.virtual_device"] == "debug"
