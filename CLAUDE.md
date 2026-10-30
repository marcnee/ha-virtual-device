# CLAUDE.md

Home Assistant custom integration `virtual_device` (repo `marcnee/ha-virtual-device`). It bundles
entities of different integrations into one virtual device. It never changes the source entities,
it creates new ones grouped under the virtual device.

## Rules

- **Do not guess.** If requirements are unclear, ask the user.
- **TDD.** Failing test first, run it and see it fail for the right reason, then the smallest
  implementation, then refactor. One small commit per green step.
- Everything (code, comments, README, UI strings) is English for now.
- All configuration happens through config/options flows. No YAML configuration, no extra web UI.
- Keep it clean and maintainable: small modules, pure logic separated from Home Assistant glue,
  no duplicated code.

## Target versions

Home Assistant **2026.10.4**, Python **3.14**. Versions are pinned in `requirements_test.txt`
and CI. When bumping, update `requirements_test.txt`, `hacs.json`, `compose.yaml`, `Dockerfile.test`,
`.github/workflows/ci.yaml` and DEVELOPMENT.md together.

## Commands

```sh
docker compose run --rm test        # pytest
docker compose run --rm lint        # ruff check + ruff format --check
python -m pytest                    # without Docker (Python 3.14 venv)
ruff check . && ruff format --check .
```

Run `ruff format .` and the tests before every commit.

## Layout

- `custom_components/virtual_device/` the integration (`manifest.json`, `config_flow.py`, ...)
- `tests/` pytest tests, one file per module
- `DEVELOPMENT.md` how to test and try it, `ROADMAP.md` planned work

## Commits

End commit messages with:

```
Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
Claude-Session: <session url>
```
