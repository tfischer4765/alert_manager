"""Fixtures for Alert Manager tests."""

from __future__ import annotations

from homeassistant.config_entries import ConfigSubentryData
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.alert_manager.const import DOMAIN, SUBENTRY_TYPE_ALERT_STATE


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load custom_components in every test."""


def alert_state(name: str, priority: int) -> ConfigSubentryData:
    """Build subentry data for an alert state."""
    return ConfigSubentryData(
        data={"name": name, "priority": priority},
        subentry_type=SUBENTRY_TYPE_ALERT_STATE,
        title=name,
        unique_id=None,
    )


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """A config entry with a red and a yellow alert."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Alert Manager",
        data={},
        subentries_data=[alert_state("Red Alert", 10), alert_state("Yellow Alert", 5)],
    )


@pytest.fixture
async def setup_entry(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> MockConfigEntry:
    """Set up the integration."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
