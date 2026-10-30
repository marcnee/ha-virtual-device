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

1. Raise `version` in `custom_components/virtual_device/manifest.json` (and commit). The ZIP
   contains the whole integration folder, including `brand/`.
2. Tag the commit with the same number and push the tag:

   ```sh
   git tag v0.1.0 && git push origin v0.1.0
   ```

The `Release` workflow runs the tests, checks that tag and manifest version match, builds the ZIP
and creates the release with generated notes.
