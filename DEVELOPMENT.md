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

```sh
pip install playwright && playwright install chromium
python scripts/render_brand.py
```

and commit the PNGs.

## Release checklist

Go through this before tagging. The automatic checks do not replace the manual ones: the tests
use a fake Home Assistant and never see the real UI.

**Code and docs**
- [ ] `CHANGELOG.md`: `[Unreleased]` renamed to the version with its date, new empty `[Unreleased]`
- [ ] `manifest.json` version raised; if stored data changed: `MINOR_VERSION`/`VERSION`, a
      migration step and its test (see "Changing the stored data")
- [ ] README and ROADMAP match what the release does
- [ ] `hacs.json` minimum Home Assistant version still correct

**Automatic checks, all green** (locally and on GitHub)
- [ ] `docker compose run --rm lint` and `docker compose run --rm test`
- [ ] `docker compose run --rm hassfest`
- [ ] `docker compose run --rm test-latest` (newest Home Assistant); the beta is informational
- [ ] GitHub: CI, Hassfest, HACS validation and the `ha-compat` workflow are green for the commit
      to be tagged
- [ ] The GitHub repository has a description and topics (`home-assistant`, `hacs`, `integration`)
      and issues enabled; HACS validation checks this

**Manual check in a real Home Assistant** (`docker compose --profile dev up homeassistant`,
start with an empty `dev/config`)
- [ ] The integration is listed with its icon; setting it up works once and a second attempt is
      refused
- [ ] *Add virtual device* with name, manufacturer and model; they show on the device page
- [ ] *Add entity from a source* for a sensor with a value template: type, name, unit and classes
      are suggested; the entity shows the transformed value and follows the source
- [ ] Switch and number from a controllable source: the actions are prefilled and really control
      the source (check the source changes, not only the virtual entity)
- [ ] Select with a mapping action and a button with an action
- [ ] *Selected attributes* lists the attributes of the source; copied attributes and attribute
      templates show up and follow the source; invalid templates show an error in the form
- [ ] The icon of the source is used; an own icon wins
- [ ] Edit an entity and a device (*Device settings*): the other devices keep running, no restart
      of the whole service
- [ ] Remove an entity and a device: they disappear from the entity and device registry, the
      source entities stay untouched
- [ ] Restart Home Assistant: everything comes back with the same entity IDs
- [ ] A source that becomes unavailable makes its virtual entity unavailable and back again
- [ ] Look at the log: no errors or warnings from `custom_components.virtual_device`

**Upgrade check** (from the first release on)
- [ ] Install the previous release in a dev instance with a few devices, then update to the new
      version: devices and entities are intact, the log shows no migration error
- [ ] Only for a data change: the migrated data in `dev/config/.storage/core.config_entries` has
      the new layout

**After tagging**
- [ ] The `Release` workflow is green and the release has `virtual_device.zip` and the
      CHANGELOG section as notes
- [ ] HACS: add the repository as a custom repository (or update), install the release, restart
      and check that the integration loads
- [ ] Open the new `[Unreleased]` section for the next changes

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

### Building a release by hand

The workflow does this on GitHub; the same steps work locally (the `gh` CLI must be logged in):

```sh
python3 scripts/release_notes.py 0.1.0 > release_notes.md      # preview the notes
(cd custom_components/virtual_device && zip -r ../../virtual_device.zip . -x "__pycache__/*")
gh release create v0.1.0 virtual_device.zip --title v0.1.0 --notes-file release_notes.md
```

Do this instead of pushing the tag, not in addition, or the workflow fails because the release
exists. Without HACS, copy `custom_components/virtual_device` into `config/custom_components/` of
the Home Assistant instance and restart.

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

To run the same check locally with Docker:

```sh
docker compose build --no-cache test-latest && docker compose run --rm test-latest   # newest release
docker compose build --no-cache test-beta   && docker compose run --rm test-beta     # newest beta
```

`--no-cache` matters: Docker would otherwise reuse the installed version of the last build. The
run prints the Home Assistant version it tested. Without Docker, use a separate environment so
that the pinned one stays untouched:

```sh
python3.14 -m venv /tmp/compat && . /tmp/compat/bin/activate
pip install pytest-homeassistant-custom-component      # newest release; add --pre for the beta
python -m pytest
```

## Hassfest

Home Assistant's own checks of `manifest.json` and the translations. The GitHub action only starts
a Docker image with the repository mounted, so the same check runs locally:

```sh
docker compose run --rm hassfest
```

It also runs on every push and weekly on GitHub. The image is not pinned, like in the action, so it
follows the newest Home Assistant checks.
