"""Pure logic: migrating the stored data of a virtual device to the current layout.

How to change the stored data after a release:

1. Raise `MINOR_VERSION` of the config flow for a compatible change (a new optional field with a
   default) or `VERSION` for a change that old data cannot be used for.
2. Add a `Step` below that leads from the previous version to the new one.
3. Add a test with data in the old layout (see tests/test_migration.py) and a CHANGELOG entry.
4. Keep tests/test_released_layouts.py green: it loads the layout of every release and checks
   that unique IDs, entity IDs, states, attributes, the device and commands stay the same.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

type Version = tuple[int, int]  # (VERSION, MINOR_VERSION) of the config entry


@dataclass(frozen=True)
class Step:
    """One migration: turns the data of a device subentry from one version into the next."""

    from_version: Version
    to_version: Version
    migrate_device: Callable[[dict[str, Any]], dict[str, Any]]


# In order, each step starting where the previous one ended. None yet: 0.1.0 (version 2.1) is the
# only layout released so far; tests/released/0.1.0.json freezes it.
STEPS: tuple[Step, ...] = ()


def migrate_device_data(
    data: Mapping[str, Any], version: Version, steps: tuple[Step, ...] = STEPS
) -> dict[str, Any]:
    """The data of a device subentry stored at `version`, migrated to the current layout."""
    migrated = deepcopy(dict(data))
    for step in sorted(steps, key=lambda step: step.from_version):
        if step.from_version >= version:
            migrated = step.migrate_device(migrated)
    return migrated
