"""The context a forwarded command runs in links back to the command that caused it."""

from homeassistant.core import Context

from custom_components.virtual_device.command_context import child_context


def test_the_child_knows_its_parent_and_keeps_the_user() -> None:
    parent = Context(user_id="a-user")

    child = child_context(parent)

    assert child.id != parent.id
    assert child.parent_id == parent.id
    assert child.user_id == "a-user"


def test_without_a_parent_the_context_is_new_and_has_no_user() -> None:
    child = child_context(None)

    assert child.parent_id is None
    assert child.user_id is None
