# Changelog

All notable changes. The section of a version is used as the text of its GitHub release (HACS
shows it when you update). Describe what changes for the people who use the integration.
Changes that need action from users go under `### Breaking` at the top of their version.

## [Unreleased]

## [0.2.0] - 2026-10-31

### Added
- **Extra sources**: a virtual entity can follow more entities than its source. The templates read
  them with `sources['sensor.x'].state`, and the entity updates when any of them changes, for
  example to join a time and an error text from two sensors into one. They are only read. A missing
  extra source raises a repair issue like a missing source; each missing source gets its own.
- The forms for the source show the current value of the source and, with *Test the templates*,
  what the value template and the attribute templates make of it, including their errors,
  before anything is saved.
- Binary sensors can have a device class (door, motion, ...), suggested from the source. Binary
  sensors you already have stay as they are; adding or editing one shows a new *Details* form.
- A repair issue appears when the source of a virtual entity does not exist (deleted or removed),
  not when it is only unavailable. Choose a new source right in the issue; nothing else of the
  entity changes. The issue goes away when the source returns. Nothing is checked while Home
  Assistant is still starting.

## [0.1.0] - 2026-10-30

First release.

### Added
- One service with any number of virtual devices; each device has a name, optional manufacturer
  and model, and its own entities.
- Entity types: sensor, binary sensor, switch, number, select and button, following a source
  entity (or one of its attributes) without ever changing it.
- Value templates (for example `18 - In Betrieb` to `In Betrieb`) and several virtual entities
  from the same source.
- Commands are forwarded through freely configurable actions; for suitable sources the actions
  are suggested.
- Settings (name, type, unit, classes, range, options, icon) are suggested from the source.
- Source attributes can be copied (all or selected) and computed with attribute templates.
- Entities show where they come from (`source_entity`, `source_attribute`, `forwards_commands`).
- Changes restart only the entities that changed.
- The activity list (logbook) shows which virtual entity forwarded a command: the change at the
  source reads "triggered by" the virtual entity, and the user who gave the command is kept.
- Automatic migration of stored data for future versions.
