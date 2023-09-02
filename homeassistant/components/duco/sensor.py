"""Support for Duco sensors."""
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DucoData
from .const import DOMAIN
from .entity import DucoEntity, DucoSingleRegisterEntityDescriptionMixin, NodeInfo
from .modbus_model import (
    PARAM_VENTILATION_PERCENTAGE,
    PARAM_VENTILATION_STATUS,
    ModuleType,
    NodeHoldingRegister,
    NodeInputRegister,
)


@dataclass
class DucoSensorEntityDescription(
    SensorEntityDescription, DucoSingleRegisterEntityDescriptionMixin
):
    """Describes a Duco sensor entity."""


TEMPERATURE = DucoSensorEntityDescription(
    key="temperature",
    register=NodeInputRegister[float](3, lambda num: num / 10.0),
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    device_class=SensorDeviceClass.TEMPERATURE,
)
CO2 = DucoSensorEntityDescription(
    key="co2",
    register=NodeInputRegister[int](4, lambda num: num),
    native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
    device_class=SensorDeviceClass.CO2,
)
HUMIDITY = DucoSensorEntityDescription(
    key="humidity",
    register=NodeInputRegister[float](5, lambda num: num / 100.0),
    native_unit_of_measurement=PERCENTAGE,
    device_class=SensorDeviceClass.HUMIDITY,
)
VENTILATION_STATUS = DucoSensorEntityDescription(
    key="status",
    name="Ventilation status",
    register=PARAM_VENTILATION_STATUS,
    device_class=SensorDeviceClass.ENUM,
)

FAN = DucoSensorEntityDescription(
    key="fan",
    name="Fan",
    register=PARAM_VENTILATION_PERCENTAGE,
    icon="mdi:fan",
    native_unit_of_measurement=PERCENTAGE,
)
VALVE = DucoSensorEntityDescription(
    key="valve",
    name="Valve Position",
    register=PARAM_VENTILATION_PERCENTAGE,
    icon="mdi:valve",
    native_unit_of_measurement=PERCENTAGE,
)

AUTO_MIN = DucoSensorEntityDescription(
    key="auto_min",
    register=NodeHoldingRegister[int](5, lambda num: num, lambda num: num),
    name="Auto min",
    native_unit_of_measurement=PERCENTAGE,
)
AUTO_MAX = DucoSensorEntityDescription(
    key="auto_max",
    register=NodeHoldingRegister[int](6, lambda num: num, lambda num: num),
    name="Auto max",
    native_unit_of_measurement=PERCENTAGE,
)


class DucoSensor(DucoEntity, SensorEntity):
    """Duco entity."""

    def __init__(
        self,
        entity_description: DucoSensorEntityDescription,
        node_info: NodeInfo,
        name_override: str | None = None,
    ) -> None:
        """Initialize the Duco entity."""
        super().__init__(node_info, entity_description, [entity_description.register])
        self.register = entity_description.register
        if name_override:
            # note: forcing attr_name to None will cause entity name to be same as device name (eg Ventilation Zone ).
            self._attr_name = name_override

    def _do_update(self) -> None:
        self._attr_native_value = self.read_register(self.register)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Duco sensors."""
    data: DucoData = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for node in data.nodes:
        if node.node_type == ModuleType.MASTER_UNIT:
            entities.append(DucoSensor(FAN, node))
        if node.node_type == ModuleType.CO2_VALVE:
            entities.append(DucoSensor(TEMPERATURE, node))
            entities.append(DucoSensor(CO2, node))
            entities.append(DucoSensor(VALVE, node))
        elif node.node_type == ModuleType.HUMIDITY_VALVE:
            entities.append(DucoSensor(TEMPERATURE, node))
            entities.append(DucoSensor(HUMIDITY, node))
            entities.append(DucoSensor(VALVE, node))
        elif node.node_type == ModuleType.SWITCH:
            entities.append(DucoSensor(TEMPERATURE, node, "Switch temperature"))

    async_add_entities(entities)
