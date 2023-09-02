"""Generic ModBus utilities."""
from __future__ import annotations

import logging
from typing import TypeVar

from homeassistant.components.modbus import (
    CALL_TYPE_REGISTER_HOLDING,
    CALL_TYPE_REGISTER_INPUT,
    CALL_TYPE_WRITE_REGISTER,
    ModbusHub,
)

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


class ModbusRegisters:
    """Values for a set of modbus registers. Retrieved by #ModbusAddressRegistry."""

    def __init__(
        self, input_registers: dict[int, int], holding_registers: dict[int, int]
    ) -> None:
        """Initialize the registers."""
        self.input_registers: dict[int, int] = input_registers
        self.holding_registers: dict[int, int] = holding_registers

    def __get_registers(self, register_type: str) -> dict[int, int]:
        if register_type == CALL_TYPE_REGISTER_HOLDING:
            return self.holding_registers
        return self.input_registers

    def read_register(self, register: int, register_type: str) -> int | None:
        """Read a single register from the cached registers."""
        return self.__get_registers(register_type).get(register)


class ModbusAddressRegistry:
    """Get a batch of modbus registers in one go."""

    def __init__(self) -> None:
        """Initialize the registry."""
        self._input_addresses: set[int] = set()
        self._holding_addresses: set[int] = set()

    def add_address(self, address: int, register_type: str):
        """Add an address to the registry."""
        registers = (
            self._input_addresses
            if register_type == CALL_TYPE_REGISTER_INPUT
            else self._holding_addresses
        )
        registers.add(address)

    @staticmethod
    def __group_consecutive(addresses: set[int]):
        sorted_addresses = sorted(addresses)
        sublist: list[int] = []
        while sorted_addresses:
            v = sorted_addresses.pop(0)

            if not sublist or sublist[-1] in [v, v - 1]:
                sublist.append(v)
            else:
                yield sublist
                sublist = [v]
        if sublist:
            yield sublist

    @staticmethod
    async def __async_read_all_registers_of_type(
        addresses: set[int], register_type: str, modbus: ModbusUtil
    ) -> dict[int, int]:
        registers: dict[int, int] = dict.fromkeys(addresses)  # type: ignore[assignment]
        consecutive_register_groups = list(
            ModbusAddressRegistry.__group_consecutive(addresses)
        )
        for consecutive_registers in consecutive_register_groups:
            first_address = consecutive_registers[0]
            responses = await modbus.read_registers(
                first_address, len(consecutive_registers), register_type
            )
            if responses:
                for response_index, response in enumerate(responses):
                    registers[consecutive_registers[response_index]] = response
        return registers

    async def async_read_all_registers(self, modbus: ModbusUtil) -> ModbusRegisters:
        """Read all known addresses from modbus."""
        return ModbusRegisters(
            await self.__async_read_all_registers_of_type(
                self._input_addresses, CALL_TYPE_REGISTER_INPUT, modbus
            ),
            await self.__async_read_all_registers_of_type(
                self._holding_addresses, CALL_TYPE_REGISTER_HOLDING, modbus
            ),
        )


class ModbusUtil:
    """Utility class for ModBus."""

    def __init__(self, slave_id: int, modbus: ModbusHub) -> None:
        """Initialize the ModBus utility."""
        super().__init__()
        self.slave_id = slave_id
        self.modbus = modbus

    async def read_register(self, register: int, register_type: str) -> int | None:
        """Read a single register from ModBus."""
        registers = await self.read_registers(register, 1, register_type)
        return registers[0] if registers else None

    async def read_registers(
        self, register: int, register_count: int, register_type: str
    ) -> list[int] | None:
        """Read a set of registers from ModBus."""
        response = await self.modbus.async_pymodbus_call(
            self.slave_id, register, register_count, register_type
        )
        res = response.registers if response else None
        for i in range(0, register_count):
            reg = register + i
            _LOGGER.debug(
                "read register %s[%s]=%s", register_type, reg, res[i] if res else None
            )
        return res

    async def write_holding_register(self, register: int, value: int):
        """Write a single register to ModBus."""
        _LOGGER.debug("writing register holding[%s]=%s", register, value)
        await self.modbus.async_pymodbus_call(
            self.slave_id, register, value, CALL_TYPE_WRITE_REGISTER
        )
