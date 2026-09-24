"""Binary sensors representing the configured alert states."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    DOMAIN as BINARY_SENSOR_DOMAIN,
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import slugify
import voluptuous as vol

from .const import (
    ATTR_ALERT_ID,
    ATTR_ALERT_IDS,
    ATTR_PRIORITY,
    CONF_PRIORITY,
    DOMAIN,
    SERVICE_CLEAR_ALERT,
    SERVICE_RESET_ALERT,
    SERVICE_SET_ALERT,
    SUBENTRY_TYPE_ALERT_STATE,
)

ALERT_ID_SCHEMA: dict[vol.Marker, Any] = {vol.Required(ATTR_ALERT_ID): cv.string}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create one binary sensor per alert state."""
    for subentry in entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_TYPE_ALERT_STATE:
            continue
        async_add_entities(
            [AlertStateBinarySensor(subentry)],
            config_subentry_id=subentry.subentry_id,
        )

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SET_ALERT, ALERT_ID_SCHEMA, "async_set_alert"
    )
    platform.async_register_entity_service(
        SERVICE_CLEAR_ALERT, ALERT_ID_SCHEMA, "async_clear_alert"
    )
    platform.async_register_entity_service(
        SERVICE_RESET_ALERT, None, "async_reset_alert"
    )


class AlertStateBinarySensor(BinarySensorEntity, RestoreEntity):
    """An alert state: on while at least one caller has set it."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, subentry: ConfigSubentry) -> None:
        """Initialize the alert state."""
        name = subentry.data[CONF_NAME]
        self._attr_name = name
        self._attr_unique_id = subentry.subentry_id
        # No device: a device belongs to a single subentry, so the alert
        # states can't share one. Prefix the entity ID instead to keep the
        # alert states grouped. Only used on first registration.
        self.entity_id = f"{BINARY_SENSOR_DOMAIN}.{DOMAIN}_{slugify(name)}"
        self._priority: int = subentry.data[CONF_PRIORITY]
        # Insertion-ordered so the attribute lists callers in the order they
        # raised the alert.
        self._alert_ids: dict[str, None] = {}

    async def async_added_to_hass(self) -> None:
        """Restore the active callers after a restart or reload."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is None:
            return
        restored = last_state.attributes.get(ATTR_ALERT_IDS)
        if isinstance(restored, list):
            self._alert_ids = dict.fromkeys(str(alert_id) for alert_id in restored)

    @property
    def is_on(self) -> bool:
        """Return true while any caller has the alert set."""
        return bool(self._alert_ids)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose priority and active callers."""
        return {
            ATTR_PRIORITY: self._priority,
            ATTR_ALERT_IDS: list(self._alert_ids),
        }

    async def async_set_alert(self, alert_id: str) -> None:
        """Register a caller as having raised this alert."""
        self._alert_ids[alert_id] = None
        self.async_write_ha_state()

    async def async_clear_alert(self, alert_id: str) -> None:
        """Withdraw a caller's alert; clears once the last caller is gone."""
        self._alert_ids.pop(alert_id, None)
        self.async_write_ha_state()

    async def async_reset_alert(self) -> None:
        """Clear the alert regardless of how many callers have set it."""
        self._alert_ids.clear()
        self.async_write_ha_state()
