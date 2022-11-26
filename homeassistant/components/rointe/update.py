"""Update entity platform for Rointe devices."""
from __future__ import annotations

import logging

from rointesdk.device import RointeDevice

from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityDescription,
)
from homeassistant.helpers.entity import EntityCategory

from .coordinator import RointeDataUpdateCoordinator
from .rointe_entity import RointeRadiatorEntity

LOGGER = logging.getLogger(__name__)


class RointeUpdateEntity(RointeRadiatorEntity, UpdateEntity):
    """Update entity."""

    def __init__(
        self,
        radiator: RointeDevice,
        coordinator: RointeDataUpdateCoordinator,
    ) -> None:
        """Init the update entity."""
        description = UpdateEntityDescription(
            key="fw_update_available",
            name="Update Available",
            device_class=UpdateDeviceClass.FIRMWARE,
            entity_category=EntityCategory.DIAGNOSTIC,
        )

        # Set the name and ID of this entity to be the radiator name/id and a prefix.
        super().__init__(
            coordinator,
            radiator,
            name=f"{radiator.name} {description.name}",
            unique_id=f"{radiator.id}-{description.key}",
        )

    @property
    def installed_version(self) -> str | None:
        """Version installed and in use."""
        return self.rointe_device.firmware_version

    @property
    def latest_version(self) -> str | None:
        """Latest version available for install."""
        return "xxx"
