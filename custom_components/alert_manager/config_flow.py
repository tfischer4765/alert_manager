"""Config flow for the Alert Manager integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector
import voluptuous as vol

from .const import CONF_PRIORITY, DOMAIN, SUBENTRY_TYPE_ALERT_STATE


class AlertManagerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Alert Manager."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create the (single) Alert Manager entry."""
        if user_input is not None:
            return self.async_create_entry(title="Alert Manager", data={})
        return self.async_show_form(step_id="user")

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return the subentry types supported by this integration."""
        return {SUBENTRY_TYPE_ALERT_STATE: AlertStateSubentryFlow}


class AlertStateSubentryFlow(ConfigSubentryFlow):
    """Add or edit an alert state."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Add a new alert state."""
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = _normalize(user_input)
            errors = self._validate(user_input, exclude_subentry_id=None)
            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(_SCHEMA, user_input or {}),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Edit an existing alert state."""
        subentry = self._get_reconfigure_subentry()
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = _normalize(user_input)
            errors = self._validate(
                user_input, exclude_subentry_id=subentry.subentry_id
            )
            if not errors:
                return self.async_update_and_abort(
                    self._get_entry(),
                    subentry,
                    title=user_input[CONF_NAME],
                    data=user_input,
                )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                _SCHEMA, user_input or subentry.data
            ),
            errors=errors,
        )

    def _validate(
        self, user_input: dict[str, Any], exclude_subentry_id: str | None
    ) -> dict[str, str]:
        """Ensure name and priority are unique among the alert states."""
        errors: dict[str, str] = {}
        name = user_input[CONF_NAME]
        if not name:
            errors[CONF_NAME] = "name_empty"
        for subentry in self._get_entry().subentries.values():
            if (
                subentry.subentry_type != SUBENTRY_TYPE_ALERT_STATE
                or subentry.subentry_id == exclude_subentry_id
            ):
                continue
            if subentry.data[CONF_NAME].casefold() == name.casefold():
                errors[CONF_NAME] = "name_exists"
            if subentry.data[CONF_PRIORITY] == user_input[CONF_PRIORITY]:
                errors[CONF_PRIORITY] = "priority_exists"
        return errors


_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): selector.TextSelector(),
        vol.Required(CONF_PRIORITY): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, step=1, mode=selector.NumberSelectorMode.BOX
            )
        ),
    }
)


def _normalize(user_input: dict[str, Any]) -> dict[str, Any]:
    """Strip the name and store the priority as an int."""
    return {
        CONF_NAME: user_input[CONF_NAME].strip(),
        CONF_PRIORITY: int(user_input[CONF_PRIORITY]),
    }
