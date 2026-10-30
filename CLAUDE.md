# CLAUDE.md

Home Assistant custom integration `virtual_device` (repo `marcnee/ha-virtual-device`). It bundles
entities of different integrations into one virtual device. It never changes the source entities,
it creates new ones grouped under the virtual device.

## Rules

- **Do not guess.** If requirements are unclear, ask the user.
- **TDD.** Failing test first, run it and see it fail for the right reason, then the smallest
  implementation, then refactor. One small commit per green step.
- **Stay within the integration.** Never change existing entities, devices, registry entries,
  settings or services of the system; only the integration's own config entry, devices and
  entities. Sources are only read. The one effect on a source is a command the user forwards with
  an action they configured. `tests/test_isolation.py` guards this; keep it green and extend it
  for new features.
- Everything (code, comments, README, UI strings) is English for now.
- All configuration happens through config/options flows. No YAML configuration, no extra web UI.
- Keep it clean and maintainable: small modules, pure logic separated from Home Assistant glue,
  no duplicated code.

## Target versions

Home Assistant **2026.10.4**, Python **3.14**. Versions are pinned in `requirements_test.txt`
and CI. When bumping, update `requirements_test.txt`, `hacs.json`, `compose.yaml`, `Dockerfile.test`, `Dockerfile.dev`,
`.github/workflows/ci.yaml` and DEVELOPMENT.md together.

## Releases and stored data

- Every change that users notice goes into `[Unreleased]` in `CHANGELOG.md`; the section of a
  version is the text of its GitHub release.
- Do not change the layout of stored data without a migration step in `migration.py`, raised
  `VERSION`/`MINOR_VERSION` and a test (see DEVELOPMENT.md).
- Released versions are frozen in `tests/released/*.json`; never edit those files and keep
  `tests/test_released_layouts.py` green. Unique IDs, entity IDs, stored keys, the attributes
  `source_entity`/`source_attribute`/`forwards_commands` and the command event are public: a
  change needs a migration and a `### Breaking` entry in the CHANGELOG (see DEVELOPMENT.md).

## Commands

```sh
scripts/check.sh
docker compose run --rm test
docker compose run --rm lint
docker compose run --rm test-latest
docker compose run --rm hassfest
python -m pytest
ruff check . && ruff format --check .
```

`scripts/check.sh` = all of the following in one go with a summary; `test` = pytest, `lint` = ruff check and format check, `test-latest` = tests against the newest
Home Assistant, `hassfest` = Home Assistant's manifest and translation checks (see
DEVELOPMENT.md); `python -m pytest` and ruff work without Docker in a Python 3.14 venv. Keep
comments out of command blocks: zsh would pass `#` on to the command.

Run `ruff format .` and the tests before every commit.

## Layout

- `custom_components/virtual_device/` the integration (`manifest.json`, ...)
  - `config_flow.py` sets up the single service; `device_flow.py` is the subentry flow that
    creates/edits one virtual device (the order of the steps). Each virtual device is a config
    subentry of the service. `flow_forms.py` has the form schemas, `flow_validation.py` the checks
    of what was entered.
  - `source_issues.py` raises repair issues for missing sources, `repairs.py` is the flow that
    fixes them; `missing_sources.py` is their pure logic, `source_exists.py` the shared check.
  - `definitions.py` reads the entity definitions from the service, `device_classes.py` lists the
    device and state classes.
  - `manager.py` starts/stops entities when the configuration changes (no reload of the service);
    `changes.py` is its pure diff logic, `attributes.py` the pure logic for copied attributes.
  - `transform.py`, `attributes.py`, `source_defaults.py`, `forwarding.py` hold the pure logic
    for templates, copied attributes and suggestions from the source.
  - `migration.py` migrates stored device data between versions (pure steps).
  - `brand/` icon PNGs; render them from `assets/icon.svg` with `scripts/render_brand.py`.
- `tests/` pytest tests, one file per module
- `CHANGELOG.md` release notes, `scripts/` helper scripts (all checks, release notes, brand images)
- `.github/workflows/` CI, hassfest, HACS validation (`validate.yaml`), release and `ha-compat`
  (newer Home Assistant versions)
- `tests/ha_config/configuration.yaml` Home Assistant configuration with demo entities, used by the
  dev instance and by `tests/test_ha_config.py`
- `.vscode/` launch configurations (debug tests, attach to Docker) and tasks; keep them matching
  `compose.yaml` and `scripts/check.sh` (`tests/test_vscode.py` checks this)
- `DEVELOPMENT.md` how to test and try it, `ROADMAP.md` planned work

## Commits

End commit messages with:

```
Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
```

No session link (`Claude-Session: ...`) in commit messages or pull requests: the repository is
public.
