"""Support for Homekit number ranges.

These are mostly used where a HomeKit accessory exposes additional non-standard
characteristics that don't map to a Home Assistant feature.
"""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DucoData
from .const import DOMAIN
from .entity import DucoEntity, DucoSingleRegisterEntityDescriptionMixin, NodeInfo
from .modbus_model import (
    PARAM_TARGET_VENTILATION_PERCENTAGE,
    ModuleType,
    NodeHoldingRegister,
)


@dataclass
class DucoNumberEntityDescription(
    NumberEntityDescription, DucoSingleRegisterEntityDescriptionMixin
):
    """Describes a Duco number entity."""


VALVE_FLOW = DucoNumberEntityDescription(
    key="fan_flow",
    name="Valve Flow",
    register=NodeHoldingRegister[int](4, lambda num: num, lambda num: num),
    native_min_value=20,
    native_max_value=200,
    native_step=5,
    native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
)

VENTILATION_TARGET = DucoNumberEntityDescription(
    key="ventilation_target",
    name="Ventilation Target",
    register=PARAM_TARGET_VENTILATION_PERCENTAGE,
    native_min_value=-1,
    native_max_value=100,
    native_step=5,
    native_unit_of_measurement=PERCENTAGE,
)

CO2_TARGET = DucoNumberEntityDescription(
    key="co2_target",
    name="CO2 Target",
    register=NodeHoldingRegister[int](1, lambda num: num, lambda num: num),
    native_min_value=0,
    native_max_value=2000,
    native_step=10,
    device_class=NumberDeviceClass.CO2,
    native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
)

HUMIDITY_TARGET = DucoNumberEntityDescription(
    key="humidity_target",
    name="Humidity Target",
    register=NodeHoldingRegister[int](2, lambda num: num, lambda num: num),
    native_min_value=0,
    native_max_value=100,
    native_step=5,
    device_class=NumberDeviceClass.HUMIDITY,
    native_unit_of_measurement=PERCENTAGE,
)


class DucoNumber(DucoEntity, NumberEntity):
    """Representation of a Number control on a homekit accessory."""

    def __init__(
        self, description: DucoNumberEntityDescription, node_info: NodeInfo
    ) -> None:
        """Initialize a Duco Number."""
        super().__init__(node_info, description, [description.register])
        self.register = description.register

    def _do_update(self) -> None:
        self._attr_native_value = self.read_register(self.register)

    async def async_set_native_value(self, value: float) -> None:
        """Set the characteristic to this value."""
        await self.write_register(self.register, int(value))  # type: ignore[arg-type]


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
            entities.append(DucoNumber(VENTILATION_TARGET, node))
        elif node.node_type == ModuleType.CO2_VALVE:
            entities.append(DucoNumber(CO2_TARGET, node))
            entities.append(DucoNumber(VALVE_FLOW, node))
            entities.append(DucoNumber(VENTILATION_TARGET, node))
        elif node.node_type == ModuleType.HUMIDITY_VALVE:
            entities.append(DucoNumber(HUMIDITY_TARGET, node))
            entities.append(DucoNumber(VALVE_FLOW, node))
            entities.append(DucoNumber(VENTILATION_TARGET, node))

    async_add_entities(entities)
