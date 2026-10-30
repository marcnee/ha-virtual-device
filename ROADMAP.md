# Roadmap

Done
- [x] Create a virtual device (config flow)
- [x] Sensor mirroring a source entity, grouped under the virtual device
- [x] Value transformation with templates (e.g. `18 - In Betrieb` -> `In Betrieb`)
- [x] Several virtual entities from the same source
- [x] Source attribute instead of state
- [x] Binary sensor

Next (test first)
- [ ] Forward commands: switch, number, select, button (design question open)
- [ ] Options flow to add, edit and remove entities
- [ ] Remove stale entities from the registry after editing
- [ ] Sensor options: unit, device class, state class (numeric values)
- [ ] README with recipes

Open questions
- How commands are forwarded (see below)
- Release/publishing process (GitHub release zip for HACS?)
