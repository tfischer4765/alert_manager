# Alert-manager

The alert manager tracks, manages and presents alert states. The integration is deliberately designed to be semantics-agnostic to enable a maximum of possible usage scenarios.

## Installation

### Manual Installation
(tbd)

### Installing via HACS
(tbd)

## Configuration

The alert manager can be configured entirely via the UI. 

In the configuration dialog, you can add an arbitrary number of different alert states. Each alert state has a name and a priority. No two alert states may have the same name or the same priority.

For each alert, a binary sensor entity of type problem will be created, which you can use in your automations to react to alert states

### Priority

Priority is an attribute of each alarm sensor. It is intended to govern the precedence of alarms. Take Star Trek as a well-known example: Red alert has a higher priority than yellow alert, so if both are active at the same time, the panels are pulsing red, not yellow.

Tho chose an example closer to people's reality of life, if a fire alarm is triggered, the door-open-cat-could-escape alarm probably shouldn't drown that out.

## Usage

The integration is controlled via service calls. The main two services are `alarm_manager.set_alarm` and `alarm_manager.clear_alarm`. Each takes an `entitiy_id` - one of the afforementioned problem sensors - and an `alarm_id` which identifies the caller wishing to set the alarm. The alarm is a classical Set-On-First/Clear-On-Last pattern: it sets as soon as the first caller logs an alarm, and doesn't clear until the last caller clears his. 


In addition to this, a service `alarm_manager.reset_alarm` is provided to manually clear an alarm of all calls.

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
  - action: alarm_manager.set_alarm
    metadata: {}
    target:
      entity_id: binary_sensor.alarm_manager_red_alert
    data: 
      alarm_id: "moisture_scullery"
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
  - action: alarm_manager.clear_alarm
    metadata: {}
    target:
      entity_id: binary_sensor.alarm_manager_red_alert
    data: 
      alarm_id: "moisture_scullery"
```

### Reacting to an alert
