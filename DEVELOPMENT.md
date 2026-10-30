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
integration → Virtual Device*. The integration folder is mounted, so after a code change run
`docker compose restart homeassistant`. `dev/` is not tracked by git.

## Release

HACS installs the `virtual_device.zip` attached to a GitHub release.

1. Raise `version` in `custom_components/virtual_device/manifest.json` (and commit).
2. Tag the commit with the same number and push the tag:

   ```sh
   git tag v0.1.0 && git push origin v0.1.0
   ```

The `Release` workflow runs the tests, checks that tag and manifest version match, builds the ZIP
and creates the release with generated notes.
