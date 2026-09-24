"""Tests for the config and subentry flows."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er

from custom_components.alert_manager.const import DOMAIN


async def test_user_flow(hass: HomeAssistant) -> None:
    """The main flow creates an empty entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Alert Manager"


async def test_single_instance(hass: HomeAssistant, setup_entry) -> None:
    """Only one entry may exist."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def _start_add(hass: HomeAssistant, entry_id: str) -> dict:
    return await hass.config_entries.subentries.async_init(
        (entry_id, "alert_state"), context={"source": SOURCE_USER}
    )


async def test_add_alert_state(hass: HomeAssistant, setup_entry) -> None:
    """A new alert state is stored with a normalized name and int priority."""
    result = await _start_add(hass, setup_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"name": "  Blue Alert ", "priority": 1.0}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"name": "Blue Alert", "priority": 1}


async def test_add_duplicate(hass: HomeAssistant, setup_entry) -> None:
    """Names (case-insensitively) and priorities must be unique."""
    result = await _start_add(hass, setup_entry.entry_id)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"name": "red alert", "priority": 5}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"name": "name_exists", "priority": "priority_exists"}

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"name": " ", "priority": 3}
    )
    assert result["errors"] == {"name": "name_empty"}

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"name": "Blue Alert", "priority": 3}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_reconfigure(hass: HomeAssistant, setup_entry) -> None:
    """Editing may keep its own name/priority but not take another's."""
    red = next(
        s for s in setup_entry.subentries.values() if s.data["name"] == "Red Alert"
    )
    result = await setup_entry.start_subentry_reconfigure_flow(hass, red.subentry_id)
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"name": "Red Alert", "priority": 5}
    )
    assert result["errors"] == {"priority": "priority_exists"}

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"name": "Red Alert", "priority": 20}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()

    assert setup_entry.subentries[red.subentry_id].data["priority"] == 20
    state = hass.states.get("binary_sensor.alert_manager_red_alert")
    assert state.attributes["priority"] == 20


async def test_remove_alert_state(hass: HomeAssistant, setup_entry) -> None:
    """Removing an alert state removes its entity."""
    red = next(
        s for s in setup_entry.subentries.values() if s.data["name"] == "Red Alert"
    )
    hass.config_entries.async_remove_subentry(setup_entry, red.subentry_id)
    await hass.async_block_till_done()

    assert er.async_get(hass).async_get("binary_sensor.alert_manager_red_alert") is None
    assert hass.states.get("binary_sensor.alert_manager_red_alert") is None
