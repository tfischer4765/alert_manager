# Alert-manager

The alert manager tracks, manages and presents alert states. The integration is deliberately designed to be semantics-agnostic to enable a maximum of possible usage scenarios.

## Installation

### Manual Installation
Copy `custom_components/alert_manager` into the `custom_components` folder of your Home Assistant configuration directory and restart Home Assistant. Then add the integration via *Settings → Devices & services → Add integration → Alert Manager*.

Requires Home Assistant 2025.4 or newer.

### Installing via HACS
Add this repository as a custom repository (type *Integration*) in HACS, install *Alert Manager* and restart Home Assistant.

## Configuration

The alert manager can be configured entirely via the UI. 

In the configuration dialog, you can add an arbitrary number of different alert states. Alert states can later be edited or removed from the integration page. Each alert state has a name and a priority. No two alert states may have the same name or the same priority.

For each alert state, a binary sensor entity of device class `problem` will be created, which you can use in your automations to react to alert states. Its entity ID is derived from the name, e.g. a state named "Red Alert" becomes `binary_sensor.alert_manager_red_alert`.

### Priority

Priority is an attribute of each alert sensor. It is a non-negative integer, where higher numbers mean higher priority, and is intended to govern the precedence of alerts. Take Star Trek as a well-known example: Red alert has a higher priority than yellow alert, so if both are active at the same time, the panels are pulsing red, not yellow.

To choose an example closer to people's reality of life, if a fire alarm is triggered, the door-open-cat-could-escape alarm probably shouldn't drown that out.

## Usage

The integration is controlled via service calls. The main two services are `alert_manager.set_alert` and `alert_manager.clear_alert`. Each takes an `entity_id` - one of the aforementioned problem sensors - and an `alert_id` which identifies the caller wishing to set the alert. The alert is a classical Set-On-First/Clear-On-Last pattern: it sets as soon as the first caller logs an alert, and doesn't clear until the last caller clears theirs. Setting an alert twice with the same `alert_id` has no additional effect, and clearing an `alert_id` that isn't set is ignored.

In addition to this, a service `alert_manager.reset_alert` is provided to manually clear an alert of all callers.

Each sensor exposes two attributes:

- `priority`: the configured priority of the alert state (higher numbers take precedence).
- `alert_ids`: the callers that currently have the alert set, in the order they set it.

Active alerts are restored after a Home Assistant restart.

## Examples

### Logging a red alert when the washing machine leaks

```yaml
triggers:
  - trigger: state
    entity_id:
      - binary_sensor.flooding_scullery
    to:
      - 'on'
conditions: []
actions:
  - action: alert_manager.set_alert
    metadata: {}
    target:
      entity_id: binary_sensor.alert_manager_red_alert
    data: 
      alert_id: "moisture_scullery"
```

```yaml
triggers:
  - trigger: state
    entity_id:
      - binary_sensor.flooding_scullery
    to:
      - 'off'
conditions: []
actions:
  - action: alert_manager.clear_alert
    metadata: {}
    target:
      entity_id: binary_sensor.alert_manager_red_alert
    data: 
      alert_id: "moisture_scullery"
```

### Reacting to an alert

## Development

```sh
python -m venv .venv
.venv/bin/pip install pytest-homeassistant-custom-component ruff
.venv/bin/pytest
.venv/bin/ruff check . && .venv/bin/ruff format --check .
```
