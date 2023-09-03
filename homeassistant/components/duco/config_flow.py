"""Config flow for Duco integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.modbus import DEFAULT_HUB
from homeassistant.const import CONF_SLAVE
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import selector

from .const import CONF_FAKE, CONF_HUB, DOMAIN, MODBUS_CONFIG_EXAMPLE, MODBUS_DOMAIN

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Duco."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            modbus_domain = self.hass.data.get(MODBUS_DOMAIN)
            if not modbus_domain:
                return self.async_abort(
                    reason="modbus_not_configured",
                    description_placeholders={"example": MODBUS_CONFIG_EXAMPLE},
                )
            modbus_hubs = list(modbus_domain.keys())
            if len(modbus_hubs) == 0:
                return self.async_abort(
                    reason="modbus_hub_not_configured",
                    description_placeholders={"example": MODBUS_CONFIG_EXAMPLE},
                )
            vol_schema = vol.Schema(
                {
                    vol.Required(CONF_HUB, default=DEFAULT_HUB): selector(
                        {"select": {"options": modbus_hubs, "mode": "dropdown"}}
                    ),
                    vol.Required(
                        CONF_SLAVE,
                        default=1,
                    ): int,
                    vol.Optional(CONF_FAKE): bool,
                }
            )

            return self.async_show_form(step_id="user", data_schema=vol_schema)

        return self.async_create_entry(title="Duco", data=user_input)
