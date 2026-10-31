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
- [x] Integration icon (`brand/`)
- [x] Migration framework for stored data, release notes from `CHANGELOG.md`
- [x] Test the templates in the source forms (preview with the current state of the source)
- [x] Repair issue with a flow to choose a new source when the source entity is missing
- [x] Released layouts are frozen in tests (`tests/released/`)
- [x] Scheduled tests against the newest Home Assistant release and beta
- [x] English translations
- [x] Release workflow (GitHub release + ZIP for HACS)
- [x] The activity list shows which virtual entity forwarded a command
- [x] Demo configuration and VS Code debugging for development

Next
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
- [ ] German translation (the lines of the template preview are made in `template_preview.py`
      and need a way to be translated, e.g. a lookup of the translations at runtime)
- [ ] Diagnostics

Ideas, not decided

Features
- Build a device from several existing entities in one go: pick many sources, get one virtual
  entity for each with type, name and settings suggested (the project's core idea, today it takes
  one pass through the forms per entity)
- Duplicate an entity (same settings and templates, new source)
- Switch, number and select without a source entity (optimistic state)
- A condition for binary sensors without writing a template (e.g. above 50)
- Apply the suggestions of a source (unit, classes) to several entities at once

Usability
- Fewer forms per entity: for simple types (binary sensor, button) merge the basics and details
- A way out of every form, since Home Assistant flows have no Back button (e.g. a *Cancel* entry)
- A summary before saving: the entities of the device with type and source
- Show template and source errors on the entity itself (an `error` attribute), not only in the log
- A repair issue also for a source that stays unavailable for a long time (after a waiting time,
  to avoid false alarms)
- README screenshots of the forms, then remove `ignore: "images"` from `validate.yaml`

Decisions
- One config entry (service) with one config subentry per virtual device, so many devices do not
  clutter the integration list. A change does not reload the service: the entity manager
  (`manager.py`) restarts only the entities whose definition changed.
- Entries from development versions before subentries (version 1) are not migrated.
