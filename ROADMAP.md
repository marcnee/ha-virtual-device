# Roadmap

Done
- [x] Create a virtual device (config flow)
- [x] Sensor and binary sensor following a source, grouped under the virtual device
- [x] Value transformation with templates (e.g. `18 - In Betrieb` -> `In Betrieb`)
- [x] Several virtual entities from the same source, source attribute instead of state
- [x] Forward commands: switch, number, select, button
- [x] Options flow to add, edit and remove entities
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
- One config entry (service) per virtual device. Config subentries (one service, many devices)
  were considered and rejected for now: more work and a full reload per change, little gain.
