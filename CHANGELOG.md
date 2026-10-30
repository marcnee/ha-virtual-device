# Changelog

All notable changes. The section of a version is used as the text of its GitHub release (HACS
shows it when you update). Describe what changes for the people who use the integration.
Changes that need action from users go under `### Breaking` at the top of their version.

## [Unreleased]

### Added
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
