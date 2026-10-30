"""Start a Python module under debugpy and say when the debugger listens.

Usage: python debug_entry.py PORT [--wait] MODULE [ARGS...]

Runs inside the debug containers (see compose.yaml). VS Code starts them as the pre-launch task
of an "Attach" configuration and waits for the line printed here before it attaches. With --wait
the module only starts once the debugger is attached.
"""

from __future__ import annotations

import runpy
import sys


def parse_args(argv: list[str]) -> tuple[int, bool, str, list[str]]:
    """The port, whether to wait for the debugger, the module and its arguments."""
    port, rest = int(argv[0]), argv[1:]
    wait = rest[0] == "--wait"
    if wait:
        rest = rest[1:]
    return port, wait, rest[0], rest[1:]


def main(argv: list[str]) -> None:
    port, wait, module, args = parse_args(argv)
    import debugpy

    debugpy.listen(("0.0.0.0", port))
    print(f"Debugger listening on port {port}", flush=True)
    if wait:
        debugpy.wait_for_client()
    sys.argv = [module, *args]
    runpy.run_module(module, run_name="__main__", alter_sys=True)


if __name__ == "__main__":
    main(sys.argv[1:])
