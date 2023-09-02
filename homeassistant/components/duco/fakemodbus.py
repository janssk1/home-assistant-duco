"""Test utility to allow testing of the Duco integration without a real Modbus device."""
from __future__ import annotations

from homeassistant.components.modbus import (
    CALL_TYPE_REGISTER_HOLDING,
    CALL_TYPE_REGISTER_INPUT,
)
from homeassistant.exceptions import ConfigEntryNotReady


class _MyModbusResponse:
    def __init__(self, registers: list[int]) -> None:
        self.registers = registers


class FakeModbus:
    """Fake Modbus class."""

    INPUT_REGISTERS = {
        10: 10,
        11: 0,
        12: 69,
        20: 12,
        21: 0,
        22: 44,
        23: 201,
        24: 3003,
        25: 8001,
        29: 1,
    }

    HOLDING_REGISTERS = {
        10: 65535,
    }

    @staticmethod
    def __create_read_responses(
        first_address: int, count: int | list[int], registers: dict[int, int]
    ):
        try:
            response = [
                registers[address]
                for address in range(first_address, first_address + int(count))  # type: ignore[arg-type]
            ]
            return _MyModbusResponse(response)
        except KeyError:
            return None

    async def async_pymodbus_call(
        self, unit: int | None, address: int, value: int | list[int], use_call: str
    ):
        """Convert async to sync pymodbus call."""
        if use_call == CALL_TYPE_REGISTER_INPUT:
            return FakeModbus.__create_read_responses(
                address, value, self.INPUT_REGISTERS
            )
        if use_call == CALL_TYPE_REGISTER_HOLDING:
            return FakeModbus.__create_read_responses(
                address, value, self.HOLDING_REGISTERS
            )
        raise ConfigEntryNotReady(f"unsupported request {use_call}")
