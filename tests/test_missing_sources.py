"""Pure logic: which sources of virtual entities are missing, and how to replace one."""

from custom_components.virtual_device.missing_sources import (
    all_sources,
    missing_sources,
    replace_source,
)


def sensor(config_id: str, source: str | None, extra: list[str] | None = None) -> dict:
    config = {"id": config_id, "platform": "sensor", "name": config_id}
    config |= {"source_entity": source} if source else {}
    return config | ({"extra_sources": extra} if extra else {})


def test_all_sources_are_the_source_and_the_extra_sources() -> None:
    assert all_sources(sensor("a", "sensor.main", ["sensor.one", "sensor.two"])) == [
        "sensor.main",
        "sensor.one",
        "sensor.two",
    ]


def test_an_entity_without_a_source_has_no_sources() -> None:
    assert all_sources(sensor("a", None)) == []


def test_a_source_that_does_not_exist_is_missing() -> None:
    definitions = {("dev", "a"): sensor("a", "sensor.gone"), ("dev", "b"): sensor("b", "sensor.ok")}

    assert missing_sources(definitions, lambda entity_id: entity_id == "sensor.ok") == {
        (("dev", "a"), "sensor.gone")
    }


def test_every_missing_extra_source_is_missing_on_its_own() -> None:
    definitions = {("dev", "a"): sensor("a", "sensor.ok", ["sensor.gone", "sensor.ok", "sensor.x"])}

    assert missing_sources(definitions, lambda entity_id: entity_id == "sensor.ok") == {
        (("dev", "a"), "sensor.gone"),
        (("dev", "a"), "sensor.x"),
    }


def test_entities_without_a_source_are_never_missing() -> None:
    assert missing_sources({("dev", "a"): sensor("a", None)}, lambda entity_id: False) == set()


def test_nothing_is_missing_when_all_sources_exist() -> None:
    definitions = {("dev", "a"): sensor("a", "sensor.ok", ["sensor.also_ok"])}

    assert missing_sources(definitions, lambda entity_id: True) == set()


def test_replacing_the_source_changes_only_that_entity() -> None:
    entities = [sensor("a", "sensor.gone"), sensor("b", "sensor.gone")]

    replaced = replace_source(entities, "a", "sensor.gone", "sensor.new")

    assert [e["source_entity"] for e in replaced] == ["sensor.new", "sensor.gone"]
    assert entities[0]["source_entity"] == "sensor.gone"


def test_replacing_an_extra_source_keeps_the_source_and_the_order() -> None:
    entities = [sensor("a", "sensor.main", ["sensor.one", "sensor.gone", "sensor.three"])]

    [replaced] = replace_source(entities, "a", "sensor.gone", "sensor.new")

    assert replaced["source_entity"] == "sensor.main"
    assert replaced["extra_sources"] == ["sensor.one", "sensor.new", "sensor.three"]
    assert entities[0]["extra_sources"] == ["sensor.one", "sensor.gone", "sensor.three"]


def test_an_extra_source_that_is_replaced_by_one_already_in_use_is_not_listed_twice() -> None:
    entities = [sensor("a", "sensor.main", ["sensor.one", "sensor.gone"])]

    [replaced] = replace_source(entities, "a", "sensor.gone", "sensor.one")

    assert replaced["extra_sources"] == ["sensor.one"]
