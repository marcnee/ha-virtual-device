"""A repair issue appears for a virtual entity whose source does not exist, and goes away again."""

from typing import Any

from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

from custom_components.virtual_device.const import (
    CONF_ENTITIES,
    CONF_EXTRA_SOURCES,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_SOURCE_ENTITY,
    DOMAIN,
)

from .conftest import SetupDevice
from .helpers import subentry_by_title

SOURCE = "sensor.outside_temperature"


def status(source: str = SOURCE, extra: list[str] | None = None) -> dict[str, Any]:
    return {
        CONF_ID: "status",
        CONF_PLATFORM: "sensor",
        CONF_NAME: "Status",
        CONF_SOURCE_ENTITY: source,
        **({CONF_EXTRA_SOURCES: extra} if extra else {}),
    }


def issues(hass: HomeAssistant) -> list[ir.IssueEntry]:
    return [issue for (domain, _), issue in ir.async_get(hass).issues.items() if domain == DOMAIN]


async def test_a_missing_source_raises_an_issue(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([status()])

    [issue] = issues(hass)
    assert issue.severity is ir.IssueSeverity.WARNING
    assert issue.is_fixable
    assert issue.translation_key == "source_missing"
    assert issue.translation_placeholders == {
        "device": "Heat pump",
        "entity": "Status",
        "source": SOURCE,
    }
    assert issue.data == {
        "subentry_id": subentry_by_title(entry, "Heat pump").subentry_id,
        "config_id": "status",
        "source": SOURCE,
    }


async def test_an_existing_source_raises_no_issue(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "5")

    await setup_device([status()])

    assert issues(hass) == []


async def test_a_source_that_is_only_registered_raises_no_issue(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    """A disabled entity has no state but still exists."""
    er.async_get(hass).async_get_or_create(
        "sensor",
        "other",
        "temperature",
        suggested_object_id="outside_temperature",
        disabled_by=er.RegistryEntryDisabler.USER,
    )

    await setup_device([status()])

    assert issues(hass) == []


async def test_an_entity_without_a_source_raises_no_issue(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    await setup_device([{CONF_ID: "defrost", CONF_PLATFORM: "button", CONF_NAME: "Defrost"}])

    assert issues(hass) == []


async def test_the_issue_goes_away_when_the_source_appears(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    await setup_device([status()])

    hass.states.async_set(SOURCE, "5")
    await hass.async_block_till_done()

    assert issues(hass) == []


async def test_removing_the_source_raises_an_issue(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    registry = er.async_get(hass)
    registered = registry.async_get_or_create(
        "sensor", "other", "temperature", suggested_object_id="outside_temperature"
    )
    hass.states.async_set(SOURCE, "5")
    await setup_device([status()])
    assert issues(hass) == []

    registry.async_remove(registered.entity_id)
    hass.states.async_remove(SOURCE)
    await hass.async_block_till_done()

    assert len(issues(hass)) == 1


async def test_a_source_that_only_becomes_unavailable_raises_no_issue(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "5")
    await setup_device([status()])

    hass.states.async_set(SOURCE, "unavailable")
    await hass.async_block_till_done()

    assert issues(hass) == []


async def test_the_issue_goes_away_when_the_entity_is_removed(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([status()])
    subentry = subentry_by_title(entry, "Heat pump")

    hass.config_entries.async_update_subentry(entry, subentry, data={CONF_ENTITIES: []})
    await hass.async_block_till_done()

    assert issues(hass) == []


async def test_the_issue_goes_away_when_the_service_is_unloaded(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    entry = await setup_device([status()])

    await hass.config_entries.async_unload(entry.entry_id)

    assert issues(hass) == []


async def test_nothing_is_checked_before_home_assistant_has_started(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    """Sources of other integrations may not exist yet while Home Assistant is starting."""
    hass.set_state(CoreState.starting)

    await setup_device([status()])
    assert issues(hass) == []

    hass.set_state(CoreState.running)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    assert len(issues(hass)) == 1


async def test_a_missing_extra_source_raises_an_issue_naming_it(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "5")

    entry = await setup_device([status(extra=["sensor.error_code"])])

    [issue] = issues(hass)
    assert issue.translation_placeholders["source"] == "sensor.error_code"
    assert issue.data == {
        "subentry_id": subentry_by_title(entry, "Heat pump").subentry_id,
        "config_id": "status",
        "source": "sensor.error_code",
    }


async def test_every_missing_source_of_an_entity_gets_its_own_issue(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    await setup_device([status(extra=["sensor.error_code"])])

    named = {issue.translation_placeholders["source"] for issue in issues(hass)}

    assert named == {SOURCE, "sensor.error_code"}


async def test_the_issue_of_an_extra_source_goes_away_when_it_appears(
    hass: HomeAssistant, setup_device: SetupDevice
) -> None:
    hass.states.async_set(SOURCE, "5")
    await setup_device([status(extra=["sensor.error_code"])])

    hass.states.async_set("sensor.error_code", "133")
    await hass.async_block_till_done()

    assert issues(hass) == []
