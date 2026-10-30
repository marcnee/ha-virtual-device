# Development

Supported Home Assistant version: **2026.10.4** (Python 3.14). Tests and CI use exactly this
version (`requirements_test.txt`).

## Tests (TDD)

Write the failing test first, then the smallest change that makes it pass, then refactor.

```sh
docker compose run --rm test               # all tests
docker compose run --rm test -k sensor     # any pytest options
docker compose run --rm lint               # ruff check + format check
```

Without Docker (Python 3.14 required):

```sh
python3.14 -m venv .venv && . .venv/bin/activate
pip install -r requirements_test.txt
python -m pytest && ruff check . && ruff format --check .
```

The tests need no running Home Assistant: `pytest-homeassistant-custom-component` provides a
test `hass` instance.

## Try it in a real Home Assistant

```sh
mkdir -p dev/config
docker compose --profile dev up homeassistant
```

Open <http://localhost:8123>, finish onboarding, then *Settings → Devices & services → Add
integration → Virtual Device*, then *Add virtual device* on the entry. The integration folder is
mounted, so after a code change run `docker compose restart homeassistant`. `dev/` is not tracked
by git.

## Code layout

Pure logic is kept apart from Home Assistant glue, and each has its own test file.

| Module | Role |
|---|---|
| `config_flow.py` | Sets up the single service |
| `device_flow.py` | Subentry flow: create/edit one virtual device and its entities |
| `manager.py`, `changes.py` | Start/stop entities when the configuration changes (`changes.py` is the pure diff) |
| `entity.py` and the platform files | The virtual entities (`sensor.py`, `switch.py`, ...) |
| `transform.py`, `attributes.py` | Value and attribute templates, which attributes are copied |
| `source_defaults.py`, `forwarding.py` | Suggestions derived from the source entity |
| `actions.py` | Runs the configured actions |
| `brand/` | Integration icon shown by Home Assistant |

## Brand images

`custom_components/virtual_device/brand/` holds `icon.png` (256 px) and `icon@2x.png` (512 px).
They are rendered from `assets/icon.svg`; after editing the SVG run
`python scripts/render_brand.py` (needs Playwright with Chromium) and commit the PNGs.

## Release

HACS installs the `virtual_device.zip` attached to a GitHub release.

1. In `CHANGELOG.md` rename `[Unreleased]` to the new version with the date and start a new empty
   `[Unreleased]` section. Its text becomes the release notes shown by HACS.
2. Raise `version` in `custom_components/virtual_device/manifest.json` (and commit). The ZIP
   contains the whole integration folder, including `brand/`. A test fails if the CHANGELOG has
   no section for the manifest version.
3. Tag the commit with the same number and push the tag:

   ```sh
   git tag v0.1.0 && git push origin v0.1.0
   ```

The `Release` workflow runs the tests, checks that tag and manifest version match, builds the ZIP
and creates the release with the CHANGELOG section of that version as its notes. (GitHub's
generated notes are not used: they only list merged pull requests.)

## Changing the stored data

Once a version is released, users have devices stored in its layout. A change of that layout needs
a migration, otherwise their devices stop working after the update:

1. Raise `MINOR_VERSION` of the config flow for a compatible change (new optional field), or
   `VERSION` if old data cannot be used any more.
2. Add a `Step` to `STEPS` in `migration.py` from the previous version to the new one.
3. Write the test first: copy the pattern in `tests/test_migration.py` with data in the old layout.
   `tests/test_migration_steps.py` checks that the steps lead to the current version.
4. Describe the change in the `[Unreleased]` section of `CHANGELOG.md`.

Home Assistant calls `async_migrate_entry` when the stored version is older and refuses entries
that are newer than the code (downgrade). The migration changes nothing if one step fails.

## Newer Home Assistant versions

CI uses the pinned version. `ha-compat.yaml` also runs the tests against the newest Home Assistant
release (twice a week and on demand) and informationally against the newest beta. When it fails,
fix the incompatibility test-first, and bump the pinned version once the new release is supported
(the places are listed in `CLAUDE.md`). Dependabot only updates the GitHub actions.
