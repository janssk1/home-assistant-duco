"""Entity class for Renson ventilation unit."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .modbus_util import ModbusAddressRegistry, ModbusRegisters, ModbusUtil

_LOGGER = logging.getLogger(__name__)


class DucoCoordinator(DataUpdateCoordinator[ModbusRegisters]):
    """Define an object to hold Duco data."""

    def __init__(
        self, modbus: ModbusUtil, hass: HomeAssistant, config_entry: ConfigEntry
    ) -> None:
        """Initialize."""
        super().__init__(
            hass, _LOGGER, name=f"{DOMAIN}", update_interval=timedelta(seconds=15)
        )
        self.config_entry = config_entry
        self._attr_data = None
        self.modbus = modbus
        self.modbus_register_provider: ModbusAddressRegistry = ModbusAddressRegistry()

    async def _async_update_data(self) -> ModbusRegisters:
        return await self.modbus_register_provider.async_read_all_registers(self.modbus)
