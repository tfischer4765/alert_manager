"""Tests for the alert state binary sensors and services."""

from __future__ import annotations

from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant, State
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache,
)

from custom_components.alert_manager.const import DOMAIN

RED = "binary_sensor.alert_manager_red_alert"
YELLOW = "binary_sensor.alert_manager_yellow_alert"


async def _call(hass: HomeAssistant, service: str, entity_id: str, **data) -> None:
    await hass.services.async_call(
        DOMAIN, service, data, target={"entity_id": entity_id}, blocking=True
    )


async def test_entities_created(hass: HomeAssistant, setup_entry) -> None:
    """Each alert state gets a problem sensor exposing its priority."""
    red = hass.states.get(RED)
    assert red.state == STATE_OFF
    assert red.attributes["device_class"] == "problem"
    assert red.attributes["priority"] == 10
    assert red.attributes["alert_ids"] == []
    assert hass.states.get(YELLOW).attributes["priority"] == 5


async def test_set_on_first_clear_on_last(hass: HomeAssistant, setup_entry) -> None:
    """The alert sets with the first caller and clears with the last."""
    await _call(hass, "set_alert", RED, alert_id="a")
    assert hass.states.get(RED).state == STATE_ON

    await _call(hass, "set_alert", RED, alert_id="b")
    await _call(hass, "set_alert", RED, alert_id="a")  # repeated set is idempotent
    assert hass.states.get(RED).attributes["alert_ids"] == ["a", "b"]

    await _call(hass, "clear_alert", RED, alert_id="a")
    assert hass.states.get(RED).state == STATE_ON

    await _call(hass, "clear_alert", RED, alert_id="unknown")
    assert hass.states.get(RED).state == STATE_ON

    await _call(hass, "clear_alert", RED, alert_id="b")
    assert hass.states.get(RED).state == STATE_OFF
    assert hass.states.get(YELLOW).state == STATE_OFF


async def test_reset(hass: HomeAssistant, setup_entry) -> None:
    """Reset clears all callers."""
    await _call(hass, "set_alert", RED, alert_id="a")
    await _call(hass, "set_alert", RED, alert_id="b")
    await _call(hass, "reset_alert", RED)
    state = hass.states.get(RED)
    assert state.state == STATE_OFF
    assert state.attributes["alert_ids"] == []


async def test_restore(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """Active callers survive a restart."""
    mock_restore_cache(hass, [State(RED, STATE_ON, {"alert_ids": ["a", "b"]})])
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(RED).state == STATE_ON
    await _call(hass, "clear_alert", RED, alert_id="a")
    await _call(hass, "clear_alert", RED, alert_id="b")
    assert hass.states.get(RED).state == STATE_OFF


async def test_state_survives_reload(hass: HomeAssistant, setup_entry) -> None:
    """Adding an alert state reloads the entry without losing active alerts."""
    await _call(hass, "set_alert", RED, alert_id="a")

    result = await hass.config_entries.subentries.async_init(
        (setup_entry.entry_id, "alert_state"), context={"source": "user"}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"name": "Blue Alert", "priority": 1}
    )
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.alert_manager_blue_alert").state == STATE_OFF
    assert hass.states.get(RED).state == STATE_ON
    assert hass.states.get(RED).attributes["alert_ids"] == ["a"]
