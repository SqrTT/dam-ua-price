"""Base entity"""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DAMDataUpdateCoordinator


class DAMBaseEntity(CoordinatorEntity[DAMDataUpdateCoordinator]):
    """Representation of a base entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DAMDataUpdateCoordinator,
        entity_description: EntityDescription
    ) -> None:
        """Initiate base entity."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"${DOMAIN}-{entity_description.key}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN)},
            name=f"DAM Electricity Prices",
            entry_type=DeviceEntryType.SERVICE,
        )
