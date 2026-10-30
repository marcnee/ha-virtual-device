"""The context in which a forwarded command runs."""

from __future__ import annotations

from homeassistant.core import Context


def child_context(parent: Context | None) -> Context:
    """A new context that knows the command it was caused by and keeps its user."""
    if parent is None:
        return Context()
    return Context(parent_id=parent.id, user_id=parent.user_id)
