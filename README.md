# Alert-manager

The alert manager tracks, manages and presents alert states. The integration is deliberately designed to be semantics-agnostic to enable a maximum of possible usage scenarios.

[![GitHub Release][releases-shield]][releases-link] [![GitHub Release Date][release-date-shield]][releases-link] [![Tests][tests-shield]][tests-link] [![Validate][validate-shield]][validate-link]

[![HomeAssistant][home-assistant-shield]][home-assistant-link] [![License][license-shield]][license-link]

![Project Maintenance][maintenance-shield] [![GitHub Activity][activity-shield]][activity-link] [![Open bugs][bugs-shield]][bugs-link] [![Open enhancements][enhancements-shield]][enhancement-link]

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

## Releasing

HACS installs the integration straight from the tagged source, so a release carries
no asset of its own: the tag *is* the release.

### Versioning

`major.minor.patch`. Incrementing a position resets every lower one to zero.

| Position | Rule |
| -------- | ---- |
| `major`  | Never automatic. Decided by the maintainer. `1.0.0` additionally means the integration is considered good enough. |
| `minor`  | **Must** change on a breaking change. **May** change for a new feature. |
| `patch`  | **Must** change whenever behaviour changes — a bugfix, a changed default. |

The rules are floors, not ceilings; a larger bump is always the maintainer's call.

### Who gets a release

A GitHub pre-release is invisible to HACS unless a user has switched on beta
versions for this repository, so the tag decides the audience:

| Tag | Audience |
| --- | -------- |
| `v0.*` — including `v0.9.0-rc.1` | testers only |
| `-alpha*`, `-beta*` | testers only |
| `-rc*` from `1.0.0` on | everyone |
| no suffix from `1.0.0` on | everyone |

`v0.*` outranks `-rc*`: a `v0.9.0-rc.1` becomes `v0.9.0`, not `1.0`, so it is no
readier for general use than the version it stands for. Any suffix that is not
recognised is treated as a pre-release, so a typo like `-beat.1` stays with testers.

HACS only ever offers releases, never the state of the default branch
(`hide_default_branch` in `hacs.json`).

### Cutting a release

A tag push, but bump `version` in `custom_components/alert_manager/manifest.json`
first — the sanity check refuses a tag that disagrees with it, and no release is
created:

```bash
git tag -a v0.1.0 -m "What changed in this version"
git push origin v0.1.0
```

The release workflow takes it from there: it runs the sanity check, the linter and
the tests, and only if all of them pass does it publish the release. A failing check
therefore leaves no release behind at all.

Two conventions are enforced by that workflow:

- **The tag decides who gets the release** — see [Who gets a release](#who-gets-a-release).
- **The tag's annotation becomes the release notes**, with the generated commit
  listing appended below it. Write the changelog in `git tag -a`, not in the web UI.

The sanity check can be run locally as well:

```bash
python scripts/sanity_check.py          # working tree only
python scripts/sanity_check.py v0.2.0   # also require the tag to agree
```

With a tag it additionally requires the tag to match the manifest version and to be
greater than every existing tag (by SemVer precedence, so `v1.0.0` follows
`v1.0.0-rc1`). Either way it checks that the manifest's domain matches the
integration's directory and that `translations/en.json` is an exact copy of
`strings.json`.

The `Tests` workflow runs the sanity check, linter and tests on every push and pull
request; `Validate` runs the HACS action and Home Assistant's hassfest, on pushes and
nightly, since the HACS checks cover repository settings that can change without a
commit.

## Development

```sh
python -m venv .venv
.venv/bin/pip install pytest-homeassistant-custom-component ruff
.venv/bin/pytest
.venv/bin/ruff check . && .venv/bin/ruff format --check .
.venv/bin/python scripts/sanity_check.py
```

### Local test instance

`docker compose up -d` starts Home Assistant on <http://localhost:8123> with the integration mounted from `custom_components/alert_manager`. Configuration and state live in `dev/config` (only `configuration.yaml` is versioned). After changing the code, run `docker compose restart` to pick it up; logs are available via `docker compose logs -f`.

[releases-shield]: https://img.shields.io/github/release/tfischer4765/alert_manager.svg?style=flat-square
[releases-link]: https://github.com/tfischer4765/alert_manager/releases/latest
[release-date-shield]: https://img.shields.io/github/release-date/tfischer4765/alert_manager?style=flat-square
[tests-shield]: https://img.shields.io/github/actions/workflow/status/tfischer4765/alert_manager/tests.yml?branch=master&style=flat-square&label=tests
[tests-link]: https://github.com/tfischer4765/alert_manager/actions/workflows/tests.yml
[validate-shield]: https://img.shields.io/github/actions/workflow/status/tfischer4765/alert_manager/validate.yml?branch=master&style=flat-square&label=validate
[validate-link]: https://github.com/tfischer4765/alert_manager/actions/workflows/validate.yml
[home-assistant-shield]: https://img.shields.io/badge/Home%20Assistant-UI%20configuration-green?style=flat-square
[home-assistant-link]: https://www.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/tfischer4765/alert_manager.svg?style=flat-square
[license-link]: LICENSE
[activity-shield]: https://img.shields.io/github/commit-activity/y/tfischer4765/alert_manager.svg?style=flat-square
[activity-link]: https://github.com/tfischer4765/alert_manager/commits/master
[bugs-shield]: https://img.shields.io/github/issues/tfischer4765/alert_manager/bug?color=red&style=flat-square&label=bugs
[bugs-link]: https://github.com/tfischer4765/alert_manager/labels/bug
[enhancements-shield]: https://img.shields.io/github/issues/tfischer4765/alert_manager/enhancement?color=blue&style=flat-square&label=enhancements
[enhancement-link]: https://github.com/tfischer4765/alert_manager/labels/enhancement
[maintenance-shield]: https://img.shields.io/maintenance/yes/2026.svg?style=flat-square
