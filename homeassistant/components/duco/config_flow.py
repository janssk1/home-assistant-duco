"""Config flow for Duco integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.modbus import DEFAULT_HUB
from homeassistant.const import CONF_SLAVE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_FAKE, CONF_HUB, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HUB, default=DEFAULT_HUB, description="Modbus HUB"): str,
        vol.Required(
            CONF_SLAVE,
            vol.All(int, vol.Range(min=0, max=32)),
            description="Modbus slave id",
        ): int,
        vol.Optional(CONF_FAKE, description="Modbus slave id"): bool,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Duco."""

    VERSION = 1

    async def validate_input(
        self, hass: HomeAssistant, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate the user input allows us to connect."""
        # api = renson.RensonVentilation(data[CONF_HOST])
        #
        # if not await self.hass.async_add_executor_job(api.connect):
        #     raise CannotConnect
        #
        return {"title": "Duco"}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        return self.async_create_entry(title="Duco", data=user_input)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
