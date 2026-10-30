"""Pure logic: which virtual entities to stop and start after a configuration change."""

from __future__ import annotations

from collections.abc import Hashable, Mapping
from typing import Any

# Everything an entity is built from: what its device is made of (title, manufacturer, model, ...)
# and its own definition. Any change of either restarts the entity.
Definition = tuple[Any, Mapping[str, Any]]


def plan_changes[K: Hashable](
    running: Mapping[K, Definition], wanted: Mapping[K, Definition]
) -> tuple[set[K], set[K]]:
    """Keys to stop and keys to start. A changed definition is stopped and started again."""
    changed = {key for key in running.keys() & wanted.keys() if running[key] != wanted[key]}
    stop = (running.keys() - wanted.keys()) | changed
    start = (wanted.keys() - running.keys()) | changed
    return stop, start
