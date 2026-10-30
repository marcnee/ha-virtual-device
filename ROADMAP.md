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
- [x] Copy source attributes (none, all, selected) and mark the source (`source_entity`, `forwards_commands`)
- [x] Attribute templates (compute or rename attributes with Jinja, entered as YAML)
- [x] The icon of the source is used unless an icon is configured
- [x] Suggested actions that forward commands to the source (switch, number, select)
- [x] Manufacturer and model per virtual device, editable together with its name
- [x] Changes only restart the changed entities (no reload of the service)
- [x] A broken action only disables that command
- [x] English translations
- [x] Release workflow (GitHub release + ZIP for HACS)

Next (test first)
- [ ] More entity types, so that e.g. a light or climate can be rebuilt. Each type needs its own
      platform, a form for its attributes and one action per command, plus suggestions from the
      source like today. Order by effort, simplest first:
  - lock (lock / unlock), valve and cover (open / close / stop, optional position)
  - fan (on/off, speed, preset)
  - light (on/off, brightness, colour temperature, colour)
  - climate (mode, target temperature, presets), the largest one
  - later: water heater, humidifier, siren, vacuum, media player, date/time/text inputs
  Open question before starting, two ways to build such a type (example: a virtual light):
  - *Mirror*: pick a `light` as source. The virtual light copies its state, brightness, colours
    and supported features and passes every service call (`light.turn_on` with brightness, colour
    ...) on to the source unchanged. Little to configure and new features come for free, but it
    only works between entities of the same kind and values cannot be converted per feature.
  - *Assemble*: the virtual light is built from parts of your choice, e.g. brightness from a
    number entity, on/off from a switch, converted with templates, and one action per command.
    Full control and works across integrations (the core idea of this project), but it needs a
    long form per type and a lot more code and tests.
  Possible order: mirror first for the simple clone case, assemble per type later.
- [ ] Try it in a real Home Assistant (`docker compose --profile dev up homeassistant`) and fix findings
- [ ] German translation
- [ ] Diagnostics and repair issues (e.g. source entity missing)

Ideas, not decided
- Switch, number and select without a source entity (optimistic state)

Decisions
- One config entry (service) with one config subentry per virtual device, so many devices do not
  clutter the integration list. A change does not reload the service: the entity manager
  (`manager.py`) restarts only the entities whose definition changed.
- Entries created before subentries (version 1) are not migrated: delete them and add the
  devices again. Pre-release only.
