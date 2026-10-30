"""Pure logic: which sources of virtual entities are missing, and how to replace one."""

from custom_components.virtual_device.missing_sources import missing_sources, replace_source


def sensor(config_id: str, source: str | None) -> dict[str, str]:
    config = {"id": config_id, "platform": "sensor", "name": config_id}
    return config | ({"source_entity": source} if source else {})


def test_a_source_that_does_not_exist_is_missing() -> None:
    definitions = {("dev", "a"): sensor("a", "sensor.gone"), ("dev", "b"): sensor("b", "sensor.ok")}

    assert missing_sources(definitions, lambda entity_id: entity_id == "sensor.ok") == {
        ("dev", "a")
    }


def test_entities_without_a_source_are_never_missing() -> None:
    assert missing_sources({("dev", "a"): sensor("a", None)}, lambda entity_id: False) == set()


def test_nothing_is_missing_when_all_sources_exist() -> None:
    definitions = {("dev", "a"): sensor("a", "sensor.ok")}

    assert missing_sources(definitions, lambda entity_id: True) == set()


def test_replacing_the_source_changes_only_that_entity() -> None:
    entities = [sensor("a", "sensor.gone"), sensor("b", "sensor.gone")]

    replaced = replace_source(entities, "a", "sensor.new")

    assert [e["source_entity"] for e in replaced] == ["sensor.new", "sensor.gone"]
    assert entities[0]["source_entity"] == "sensor.gone"
