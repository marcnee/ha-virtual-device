# Virtual Device for Home Assistant

Bundle entities of **different integrations** into one **virtual device**.

- The source entities are **never modified**. New entities are created and grouped under the
  virtual device. The integration only touches its own entities, devices and settings; the
  rest of your system stays as it is. The one effect on a source is a command you forward to it
  with an action you configured.
- **Transform values** with a template, for example `18 - In Betrieb` becomes `In Betrieb`.
- Build **several virtual entities from the same source** (a text and a number, say).
- **Forward commands** to the source integration with ordinary Home Assistant actions.
- Everything is configured in the UI. No YAML.

Requires Home Assistant 2026.10 or newer.

## Installation

**HACS:** add this repository as a custom repository (type *Integration*), install
*Virtual Device*, restart Home Assistant.

**Manual:**

1. Download `virtual_device.zip` from the
   [latest release](https://github.com/marcnee/ha-virtual-device/releases/latest).
2. Create the folder `config/custom_components/virtual_device` in your Home Assistant
   configuration directory (the one with `configuration.yaml`). Create `custom_components` first
   if it does not exist.
3. Unpack the ZIP into that folder. The files (`manifest.json`, `__init__.py`, ...) have to be
   directly in `virtual_device`, not in a further subfolder. For example:

   ```sh
   unzip virtual_device.zip -d config/custom_components/virtual_device
   ```

   With Home Assistant OS use the *Samba share*, *File editor* or *Studio Code Server* add-on
   instead of the command line; in a container, put the folder into the volume mounted at
   `/config`.
4. Restart Home Assistant, then *Settings → Devices & services → Add integration → Virtual
   Device*.

To update, replace the files in the same folder with those of the new release and restart. If you
prefer the source, copy the folder `custom_components/virtual_device` of this repository instead
of the ZIP.

## Usage

1. *Settings → Devices & services → Add integration → Virtual Device*. This sets up the service
   once; all virtual devices live under this single entry.
2. Click **Add virtual device** on the entry and enter a device name. Manufacturer and model are
   optional and shown on the device page.
3. **Add entity from a source**: pick the source entity (and optional attribute and template).
   Type, name, unit, device class, number range and select options are suggested from it and can be
   changed. Or use **Add entity manually**: type and name first, then the source. Use this for
   buttons, which need no source.
4. **Save and finish**. The entities appear under the new virtual device.

To change a device, open its menu on the entry and choose **Edit virtual device**; delete it there
too. In the menu you can add, edit and remove entities, and **Device settings** changes the name,
manufacturer and model. Changes only apply after *Save and finish*. Removed entities are deleted
from the entity registry. You can add as many virtual devices as you like.

Saving a change does not reload the service: only the entities whose settings changed are
restarted (briefly unavailable, same entity ID), all other entities and devices keep running.

## Entity types

| Type | Shows | Commands |
|---|---|---|
| Sensor | Text or value of the source, optional unit and classes | none |
| Binary sensor | on/off derived from the source, optional device class (door, motion, ...) | none |
| Switch | on/off derived from the source | actions for turn on / turn off |
| Number | Number with min, max, step and unit | action with `{{ value }}` |
| Select | One of your options | action with `{{ option }}` |
| Button | Nothing | action when pressed (no source needed) |

Every entity can have its own icon. A virtual entity is *unavailable* while its source is
unavailable, and *unknown* while the source is unknown, has no such attribute or the template
fails or returns nothing.

If the source does not exist at all (deleted, or its integration removed), Home Assistant shows a
repair issue: choose a new source there, or wait for the source to return. The virtual entity
stays unavailable meanwhile. Nothing is checked while Home Assistant starts, and the source
being only unavailable raises no issue.

Binary sensors and switches treat the (transformed) value `on`, `true`, `1` and `yes` as on and
everything else as off. Use a template for other conventions.

If a sensor has a unit, device class or state class, its value must be numeric (Home Assistant
requires it). Non-numeric values show as *unknown* and are logged. Leave those fields empty for text.

## Transforming values

The optional template sees `value` (the source state, or the chosen attribute), `state`,
`attributes` and `sources` (the extra sources, see below).

| Goal | Template |
|---|---|
| `18 - In Betrieb` to `In Betrieb` | `{{ value.split(' - ', 1)[-1] }}` |
| Only the code `18` | `{{ value.split(' - ')[0] }}` |
| Running? (binary sensor) | `{{ value.startswith('18') }}` |
| Table lookup | `{{ {'18': 'In Betrieb', '19': 'Standby'}.get(value.split(' - ')[0], value) }}` |

For two entities from one status, add two sensors with the same source and different templates.

### Combining several entities

Choose **Extra sources** in the source form to make a value from more than one entity. The
template reads them in `sources`, by entity ID, and the virtual entity updates whenever the source
or any extra source changes. Example: a sensor that joins the time and the text of the last error
of a boiler (source: the time entity, extra source: the error code entity):

```jinja
{% set code = sources['sensor.boiler_error_code'].state %}
{{ value }} - {{ code.split(' - ')[0] }} - {{ code.split(':', 1)[1] }}
```

gives `29.10.2026 11:14:00 - 133 - Safety time exceeded`. The extra sources are only read, never
changed. An extra source that does not exist makes the template fail (the value is *unknown*,
the failure is logged) and raises a repair issue, like a missing source. The entity is
unavailable only when its source is.

The form shows the current value of the source and what the templates make of it. Tick *Test the
templates* and submit to see the result for what you just entered; the form stays open until you
submit without it. Errors of a template are shown there instead of only in the log. Nothing is
stored by the test.

## Forwarding commands

When you add a switch, number or select whose source can be controlled that way, the action forms
are prefilled with an action that passes the command on to the source: `homeassistant.turn_on` /
`turn_off` for `switch`, `input_boolean`, `light` and `fan`; `number.set_value` /
`input_number.set_value` for numbers; `select.select_option` / `input_select.select_option` for
selects. The suggestion is only made when adding, never when editing, and you can change or clear
it. For any other source write the action yourself (see below).

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

In the activity list (logbook) you can see who changed the source: each forwarded command is
logged for the virtual entity ("Heat pump Power forwarded the on command to switch.heatpump"), and
the change at the source is shown as triggered by that entity. The user who gave the command
stays attached, whether it came from the dashboard, an automation or a voice assistant.

Switches, numbers and selects do not change their own state after a command. They follow the
source, so the state you see is the one the device really reports.

## Attributes and where an entity is wired to

Every virtual entity shows where it comes from in its attributes:

| Attribute | Meaning |
|---|---|
| `source_entity` | The entity it follows |
| `source_attribute` | The attribute it reads instead of the state (only if set) |
| `forwards_commands` | `true` if at least one action is configured, so commands are forwarded |

An entity with a source uses the source's icon unless you set an icon of its own. (Home Assistant
only puts an icon into a state if it was customized; default icons of a type or device class are
not copied.)

The source forms also offer **Copy source attributes**: none (default), all, or selected
attributes (a next step offers the attributes the source has right now; you can also type
names). Copied attributes follow the source. Attributes Home Assistant sets itself (`friendly_name`, `icon`, `unit_of_measurement`, `device_class`, `state_class`,
`entity_picture`, `supported_features`, `options`, `min`, `max`, `step`, `mode`) and the three
attributes above are never copied.

**Attribute templates** compute or rename attributes. In the source form enter YAML with one
attribute name and one template per line:

```yaml
fehlercode: "{{ attributes.error_code | int }}"
status_text: "{{ value.split(' - ', 1)[-1] }}"
```

The templates see `value` (state or chosen attribute), `state`, `attributes` and `sources`, like
the value template. Numbers stay numbers. A template overrides a copied attribute of the same name; one that
renders `none` or fails (it is logged) only leaves out its attribute. The reserved names above
cannot be used.

## Updating

Update through HACS; the release notes are shown there. Your devices are migrated automatically
when the stored layout changes. Home Assistant refuses entries that were saved by a newer version,
so downgrade only together with a backup.

## Limitations (see ROADMAP.md)

- Six entity types only (sensor, binary sensor, switch, number, select, button). Lights, climate
  and others cannot be rebuilt yet.
- Commands reach the source only through the actions you configure (or the suggested ones). A
  switch, number or select never assumes a new state; it follows the source.
- The forms have no *Back* button (Home Assistant's dialogs have none). A form of an entity has to
  be finished to return to the menu. Closing the dialog with the X cancels everything that was
  not saved with *Save and finish*.
- A device has no icon of its own, because Home Assistant has none for devices. Entities do.
- Only English texts for now.

## Support, contributing, license

Questions and bug reports are welcome as
[GitHub issues](https://github.com/marcnee/ha-virtual-device/issues); please include your Home
Assistant version and the relevant log lines (`custom_components.virtual_device`). To work on the
code, see [DEVELOPMENT.md](DEVELOPMENT.md): tests come first, and `scripts/check.sh` runs all checks.
Released under the [MIT license](LICENSE).
