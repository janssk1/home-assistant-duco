"""DUCO specific modbus utilities. The ModBus registers are split per node."""
from __future__ import annotations

from abc import ABC
from collections.abc import Callable
from enum import Enum
import logging
from typing import Generic, TypeVar

from homeassistant.components.modbus import (
    CALL_TYPE_REGISTER_HOLDING,
    CALL_TYPE_REGISTER_INPUT,
)

from .modbus_util import ModbusRegisters, ModbusUtil

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


class NodeRegister(ABC, Generic[T]):
    """Representation of a Modbus register in a node."""

    def __init__(
        self,
        register: int,
        from_int: Callable[[int], T] | None,
        read_register_type: str = CALL_TYPE_REGISTER_INPUT,
    ) -> None:
        """Initialize the register."""
        self.read_register_type = read_register_type
        self.from_int = from_int
        self.register = register

    def read(self, modbus: ModbusRegisters, node_offset: int) -> T:
        """Read the register for a specific node from modbus."""
        register = modbus.read_register(
            self.get_address(node_offset), self.read_register_type
        )
        return self._convert_value(register)

    def _convert_value(self, register):
        converted = self.from_int(register) if register is not None else None
        _LOGGER.debug(f"Converted value: {converted}")
        return converted

    async def async_read(self, modbus: ModbusUtil, node_offset: int) -> T:
        """Read the register for a specific node from modbus."""
        register = await modbus.read_register(
            self.get_address(node_offset), self.read_register_type
        )
        return self._convert_value(register)

    def get_address(self, node_offset):
        """Get the address of the register for a specific node."""
        return node_offset + self.register


class NodeHoldingRegister(NodeRegister[T]):
    """Representation of a redModbus holding register in a node."""

    def __init__(
        self,
        register: int,
        from_int: Callable[[int], T] | None,
        to_int: Callable[[T], int],
    ) -> None:
        """Initialize the register."""
        super().__init__(register, from_int, CALL_TYPE_REGISTER_HOLDING)
        self.to_int = to_int

    async def write(self, modbus: ModbusUtil, value: T, node_offset: int = 10):
        """Write the register for a specific node to modbus."""
        await modbus.write_holding_register(
            node_offset + self.register, self.to_int(value)
        )


class NodeInputRegister(NodeRegister[T]):
    """Representation of a Modbus input register in a node."""

    def __init__(self, register: int, from_int: Callable[[int], T]) -> None:
        """Initialize the register."""
        super().__init__(register, from_int)


class ModuleType(Enum):
    """Enum with all module types."""

    MASTER_UNIT = 10
    CO2_VALVE = 12
    HUMIDITY_VALVE = 13
    SWITCH = 14


class VentilationStatus(Enum):
    """Enum with all level values."""

    AUTO = 0
    HIGH_TEMP_10M = 1
    HIGH_TEMP_20M = 2
    HIGH_TEMP_30M = 3
    MAN_LOW = 4
    MAN_MID = 5
    MAN_HIGH = 6
    AWAY = 7
    TEMP_LOW = 8
    TEMP_MID = 9
    TEMP_HIGH = 10
    ERROR = 99


PARAM_MODULE_TYPE = NodeInputRegister[ModuleType](0, ModuleType)

PARAM_VENTILATION_STATUS = NodeInputRegister[VentilationStatus](1, VentilationStatus)
PARAM_VENTILATION_PERCENTAGE = NodeInputRegister[int](2, lambda num: num)
PARAM_LOCALIZATION_NUMBER = NodeInputRegister[int](9, lambda num: num)

PARAM_TARGET_VENTILATION_PERCENTAGE = NodeHoldingRegister[int](
    0, lambda num: -1 if num == 65535 else num, lambda num: 65535 if num == -1 else num
)
