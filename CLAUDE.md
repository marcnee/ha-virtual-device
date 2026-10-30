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

## Releases and stored data

- Every change that users notice goes into `[Unreleased]` in `CHANGELOG.md`; the section of a
  version is the text of its GitHub release.
- Do not change the layout of stored data without a migration step in `migration.py`, raised
  `VERSION`/`MINOR_VERSION` and a test (see DEVELOPMENT.md).

## Commands

```sh
docker compose run --rm test        # pytest
docker compose run --rm lint        # ruff check + ruff format --check
docker compose run --rm test-latest # tests against the newest Home Assistant (see DEVELOPMENT.md)
docker compose run --rm hassfest    # Home Assistant's manifest and translation checks
python -m pytest                    # without Docker (Python 3.14 venv)
ruff check . && ruff format --check .
```

Run `ruff format .` and the tests before every commit.

## Layout

- `custom_components/virtual_device/` the integration (`manifest.json`, ...)
  - `config_flow.py` sets up the single service; `device_flow.py` is the subentry flow that
    creates/edits one virtual device. Each virtual device is a config subentry of the service.
  - `manager.py` starts/stops entities when the configuration changes (no reload of the service);
    `changes.py` is its pure diff logic, `attributes.py` the pure logic for copied attributes.
  - `transform.py`, `attributes.py`, `source_defaults.py`, `forwarding.py` hold the pure logic
    for templates, copied attributes and suggestions from the source.
  - `migration.py` migrates stored device data between versions (pure steps).
  - `brand/` icon PNGs; render them from `assets/icon.svg` with `scripts/render_brand.py`.
- `tests/` pytest tests, one file per module
- `CHANGELOG.md` release notes, `scripts/` helper scripts (release notes, brand images)
- `.github/workflows/` CI, hassfest, HACS validation (`validate.yaml`), release and `ha-compat`
  (newer Home Assistant versions)
- `DEVELOPMENT.md` how to test and try it, `ROADMAP.md` planned work

## Commits

End commit messages with:

```
Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
Claude-Session: <session url>
```
