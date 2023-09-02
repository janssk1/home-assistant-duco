"""Support for Homekit number ranges.

These are mostly used where a HomeKit accessory exposes additional non-standard
characteristics that don't map to a Home Assistant feature.
"""
from __future__ import annotations

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DucoData
from .const import DOMAIN
from .entity import DucoEntity, NodeInfo
from .modbus_model import (
    PARAM_TARGET_VENTILATION_PERCENTAGE,
    PARAM_VENTILATION_STATUS,
    ModuleType,
    NodeHoldingRegister,
    VentilationStatus,
)

VENTILATION_STATUS_TO_WRITE_COMMAND = {
    VentilationStatus.AUTO: 5,
    VentilationStatus.AWAY: 6,
    VentilationStatus.MAN_LOW: 2,
    VentilationStatus.MAN_MID: 3,
    VentilationStatus.MAN_HIGH: 4,
}


def __get_write_status(ventilation_status: VentilationStatus) -> int:
    res = VENTILATION_STATUS_TO_WRITE_COMMAND[ventilation_status]
    if res is None:
        raise ValueError(f"Ventilation status {ventilation_status} is not writable")
    return res


PARAM_VENTILATION_ACTION = NodeHoldingRegister[VentilationStatus](
    9, None, __get_write_status
)

VENTILATION_STATUS = SelectEntityDescription(
    key="status", name="Ventilation status", options=[e.name for e in VentilationStatus]
)


class DucoVentilationStatusSelect(DucoEntity, SelectEntity):
    """Representation of a Select control for Duco."""

    def __init__(
        self, description: SelectEntityDescription, node_info: NodeInfo
    ) -> None:
        """Initialize the Select control."""
        super().__init__(node_info, description, [PARAM_VENTILATION_STATUS])
        self._attr_current_option = None

    def _do_update(self) -> None:
        self._attr_current_option = self.read_register(PARAM_VENTILATION_STATUS)

    async def async_select_option(self, option: str) -> None:
        """Set the option."""
        await self.write_register(
            PARAM_TARGET_VENTILATION_PERCENTAGE, -1
        )  # Disable explicit override
        await self.write_register(PARAM_VENTILATION_ACTION, VentilationStatus[option])


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Duco number entities."""
    data: DucoData = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for node in data.nodes:
        if node.node_type == ModuleType.MASTER_UNIT:
            entities.append(DucoVentilationStatusSelect(VENTILATION_STATUS, node))
        elif node.node_type == ModuleType.CO2_VALVE:
            entities.append(DucoVentilationStatusSelect(VENTILATION_STATUS, node))
        elif node.node_type == ModuleType.HUMIDITY_VALVE:
            entities.append(DucoVentilationStatusSelect(VENTILATION_STATUS, node))

    async_add_entities(entities)
