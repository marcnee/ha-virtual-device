# Roadmap

Done
- [x] Create virtual devices (one service, one config subentry per device)
- [x] Sensor and binary sensor following a source, grouped under the virtual device
- [x] Value transformation with templates (e.g. `18 - In Betrieb` -> `In Betrieb`)
- [x] Several virtual entities from the same source, source attribute instead of state
- [x] Forward commands: switch, number, select, button
- [x] Subentry flow to add, edit and remove entities
- [x] Stale entities are removed from the registry
- [x] Sensor options: unit, device class, state class
- [x] Suggested settings from the source entity (name, type, unit, classes, range, options)
- [x] Optional icon per virtual entity
- [x] A broken action only disables that command
- [x] English translations
- [x] Release workflow (GitHub release + ZIP for HACS)

Next (test first)
- [ ] Try it in a real Home Assistant (`docker compose --profile dev up homeassistant`) and fix findings
- [ ] German translation
- [ ] Diagnostics and repair issues (e.g. source entity missing)

Ideas, not decided
- Switch, number and select without a source entity (optimistic state)

Decisions
- One config entry (service) with one config subentry per virtual device, so many devices do not
  clutter the integration list. Trade-off: any change reloads the whole service.
- Entries created before subentries (version 1) are not migrated: delete them and add the
  devices again. Pre-release only.
