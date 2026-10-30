# Virtual Device for Home Assistant

Bundle entities of **different integrations** into one **virtual device**.

- The source entities are **never modified**. New entities are created and grouped under the
  virtual device.
- **Transform values** with a template, for example `18 - In Betrieb` becomes `In Betrieb`.
- Build **several virtual entities from the same source** (a text and a number, say).
- **Forward commands** to the source integration with ordinary Home Assistant actions.
- Everything is configured in the UI. No YAML.

Requires Home Assistant 2026.10 or newer.

## Installation

**HACS:** add this repository as a custom repository (type *Integration*), install
*Virtual Device*, restart Home Assistant.

**Manual:** copy `custom_components/virtual_device` into your `config/custom_components/`
folder and restart.

## Usage

1. *Settings → Devices & services → Add integration → Virtual Device*, enter a device name.
2. Click **Configure** on the new entry.
3. **Add entity**: choose a type and a name, then the source entity and an optional template,
   then the type specific details.
4. **Save and finish**. The device reloads and the entities appear under the virtual device.

Edit or remove entities the same way. Changes only apply after *Save and finish*. Removed
entities are deleted from the entity registry. You can create as many virtual devices as you like.

## Entity types

| Type | Shows | Commands |
|---|---|---|
| Sensor | Text or value of the source | none |
| Binary sensor | on/off derived from the source | none |
| Switch | on/off derived from the source | actions for turn on / turn off |
| Number | Number with min, max, step and unit | action with `{{ value }}` |
| Select | One of your options | action with `{{ option }}` |
| Button | Nothing | action when pressed (no source needed) |

A virtual entity is *unavailable* while its source is unavailable, and *unknown* while the source
is unknown, has no such attribute or the template fails or returns nothing.

Binary sensors and switches treat the (transformed) value `on`, `true`, `1` and `yes` as on and
everything else as off. Use a template for other conventions.

## Transforming values

The optional template sees `value` (the source state, or the chosen attribute), `state` and
`attributes`.

| Goal | Template |
|---|---|
| `18 - In Betrieb` to `In Betrieb` | `{{ value.split(' - ', 1)[-1] }}` |
| Only the code `18` | `{{ value.split(' - ')[0] }}` |
| Running? (binary sensor) | `{{ value.startswith('18') }}` |
| Table lookup | `{{ {'18': 'In Betrieb', '19': 'Standby'}.get(value.split(' - ')[0], value) }}` |

For two entities from one status, add two sensors with the same source and different templates.

## Forwarding commands

Actions are normal Home Assistant actions, as in scripts. Their templates can use `source_entity`,
`source_state` and, depending on the type, `value` (number) or `option` (select).

A select showing `In Betrieb` / `Standby` and sending the control values 18 / 19:

```yaml
- action: number.set_value
  target:
    entity_id: number.heatpump_mode
  data:
    value: "{{ {'In Betrieb': 18, 'Standby': 19}[option] }}"
```

Passing a number through unchanged:

```yaml
- action: number.set_value
  target:
    entity_id: "{{ source_entity }}"
  data:
    value: "{{ value }}"
```

Switches, numbers and selects do not change their own state after a command. They follow the
source, so the state you see is the one the device really reports.

## Limitations (see ROADMAP.md)

- Sensors have no unit, device class or state class options yet.
- Only English texts for now.
