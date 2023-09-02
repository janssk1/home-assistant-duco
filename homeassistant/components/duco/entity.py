"""Entity class for Duco ventilation unit."""
from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
import logging

from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODEL_NAME
from .coordinator import DucoCoordinator
from .modbus_model import ModuleType, NodeHoldingRegister, NodeRegister, T

_LOGGER = logging.getLogger(__name__)


@dataclass
class DucoSingleRegisterEntityDescriptionMixin:
    """Mixin for required keys."""

    register: NodeRegister


class DucoEntity(CoordinatorEntity[DucoCoordinator]):
    """Duco entity."""

    def __init__(
        self,
        node_info: NodeInfo,
        entity_description: EntityDescription,
        read_registers: list[NodeRegister],
    ) -> None:
        """Initialize the Duco entity."""
        super().__init__(node_info.coordinator)
        self.read_registers = read_registers
        self.zone_id = node_info.location_id
        self.node_id = node_info.node_id
        self.modbus = node_info.coordinator.modbus
        self.entity_description = entity_description

        focus_box_device_id = f"slave_{self.modbus.slave_id}"
        device_id = focus_box_device_id
        device_name = f"{MODEL_NAME}"
        via_device = None
        unique_id = f"{node_info.node_type.name}_{self.entity_description.key}".lower()
        if self.zone_id is not None:
            # zoned device
            device_id = f"{focus_box_device_id}_zone{self.zone_id}"
            device_name = f"Ventilation Zone {self.zone_id}"
            via_device = (DOMAIN, focus_box_device_id)
            unique_id = f"{unique_id}_zone{self.zone_id}"
        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            manufacturer="Duco",
            model=MODEL_NAME,
            name=device_name,
        )
        if via_device:
            self._attr_device_info["via_device"] = via_device

        self._attr_has_entity_name = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._do_update()
        self.async_write_ha_state()

    @abstractmethod
    def _do_update(self):
        pass

    def read_register(self, register: NodeRegister[T]):
        """Read a value from a register."""
        return self.__convert_to_ha_state(
            register.read(self.coordinator.data, self.node_id)
        )

    def __convert_to_ha_state(self, response: T):
        if isinstance(response, Enum):
            return response.name
        return response

    async def async_read_register(self, register: NodeRegister[T]):
        """Read a value from a register."""
        return self.__convert_to_ha_state(
            await register.async_read(self.modbus, self.node_id)
        )

    async def write_register(self, register: NodeHoldingRegister[T], value: T):
        """Write a value to a register."""
        return await register.write(self.modbus, value, self.node_id)

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        for reg in self.read_registers:
            self.coordinator.modbus_register_provider.add_address(
                reg.get_address(self.node_id), reg.read_register_type
            )


@dataclass
class NodeInfo:
    """Duco data class."""

    coordinator: DucoCoordinator
    node_type: ModuleType
    node_id: int
    location_id: int | None
