"""Which virtual entities have to be stopped and started after a configuration change."""

from custom_components.virtual_device.changes import plan_changes


def test_nothing_changes() -> None:
    running = {"a": ("Heat pump", {"name": "A"})}

    assert plan_changes(running, dict(running)) == (set(), set())


def test_new_definitions_are_started() -> None:
    assert plan_changes({}, {"a": ("Heat pump", {"name": "A"})}) == (set(), {"a"})


def test_missing_definitions_are_stopped() -> None:
    assert plan_changes({"a": ("Heat pump", {"name": "A"})}, {}) == ({"a"}, set())


def test_a_changed_definition_is_restarted() -> None:
    old = {"a": ("Heat pump", {"name": "A"}), "b": ("Heat pump", {"name": "B"})}
    new = {"a": ("Heat pump", {"name": "A2"}), "b": ("Heat pump", {"name": "B"})}

    assert plan_changes(old, new) == ({"a"}, {"a"})


def test_a_renamed_device_restarts_its_entities() -> None:
    old = {"a": ("Heat pump", {"name": "A"})}
    new = {"a": ("Heater", {"name": "A"})}

    assert plan_changes(old, new) == ({"a"}, {"a"})
