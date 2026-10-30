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
- [x] English translations
- [x] Release workflow (GitHub release + ZIP for HACS)

Next (test first)

- [ ] Try it in a real Home Assistant (`docker compose --profile dev up homeassistant`) and fix findings
- [ ] German translation
- [ ] Optional icon per virtual entity
- [ ] Diagnostics and repair issues (e.g. source entity missing)

Ideas, not decided
- Switch, number and select without a source entity (optimistic state)
