"""The duco integration."""
from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.components.modbus import ModbusHub, get_hub
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SLAVE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_FAKE, CONF_HUB, DOMAIN
from .coordinator import DucoCoordinator
from .entity import NodeInfo
from .fakemodbus import FakeModbus
from .modbus_model import (
    PARAM_LOCALIZATION_NUMBER,
    PARAM_MODULE_TYPE,
    ModuleType,
)
from .modbus_util import (
    ModbusUtil,
)

_LOGGER = logging.getLogger(__name__)

# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
]


@dataclass
class DucoData:
    """Duco data class."""

    nodes: list[NodeInfo]


def __get_hub(hass: HomeAssistant, entry: ConfigEntry):
    fake: bool | None = entry.data.get(CONF_FAKE)
    if fake:
        _LOGGER.warning("******************  Using fake ModBus ******************")
        return FakeModbus()
    hub_name = entry.data[CONF_HUB]
    hub: ModbusHub = get_hub(hass, hub_name)
    if not hub:
        raise ConfigEntryNotReady(
            f"Modbus hub {hub_name} not configured. Check modus section in configuration.yaml"
        )
    return hub


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    hub = __get_hub(hass, entry)
    slave_id = entry.data[CONF_SLAVE]
    modbus = ModbusUtil(slave_id, hub)
    nodes: list[NodeInfo] = []
    coordinator = DucoCoordinator(modbus, hass, entry)
    master = await PARAM_MODULE_TYPE.async_read(modbus, 10)
    if master:
        nodes.append(NodeInfo(coordinator, ModuleType.MASTER_UNIT, 10, None))
        for i in range(2, 7):
            node_id = i * 10
            module_type: ModuleType = await PARAM_MODULE_TYPE.async_read(
                modbus, node_id
            )
            if module_type:
                _LOGGER.info(f"Detected {module_type.name}")
                location: int = await PARAM_LOCALIZATION_NUMBER.async_read(
                    modbus, node_id
                )
                nodes.append(NodeInfo(coordinator, module_type, node_id, location))

        await coordinator.async_config_entry_first_refresh()

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = DucoData(nodes)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        return True
    raise ConfigEntryNotReady(
        f"Modbus slave {slave_id} not reachable. Check the logs for more information."
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
