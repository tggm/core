"""Provides the Rointe DataUpdateCoordinator."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from rointesdk.device import RointeDevice

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, LOGGER, PLATFORMS, ROINTE_API_REFRESH_SECONDS
from .device_manager import RointeDeviceManager


class RointeDataUpdateCoordinator(DataUpdateCoordinator[dict[str, RointeDevice]]):
    """Rointe data coordinator."""

    def __init__(
        self, hass: HomeAssistant, device_manager: RointeDeviceManager
    ) -> None:
        """Initialize Rointe data updater."""
        self.device_manager = device_manager
        self.unregistered_keys: dict[str, dict[str, RointeDevice]] = {}

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=ROINTE_API_REFRESH_SECONDS),
        )

        self.unregistered_keys = {platform: {} for platform in PLATFORMS}

    async def _async_update_data(self) -> dict[str, RointeDevice]:
        """Fetch data from API."""

        devices = await self.device_manager.update()

        for platform in PLATFORMS:
            self.unregistered_keys[platform].update(
                {
                    device_id: device
                    for device_id, device in devices.items()
                    if device_id not in self.unregistered_keys[platform]
                }
            )

        for device in devices.values():
            device_update_info(self.hass, device)

        return devices

    @callback
    def add_entities_for_seen_keys(
        self,
        async_add_entities: AddEntitiesCallback,
        entity_constructor_list: list[Any],
        platform: str,
    ) -> None:
        """
        Add entities for new devices, for a given platform.

        Called from a platform's `async_setup_entry`.
        """

        @callback
        def _add_entities_for_unregistered_keys() -> None:
            """Handle creating new entities."""
            new_entities: list = []
            discovered_devices: dict[str, RointeDevice] = self.data

            if discovered_devices:
                for device_id, device in discovered_devices.items():
                    if device_id in self.unregistered_keys[platform]:
                        entities_list = [
                            constructor(device, self)
                            for constructor in entity_constructor_list
                        ]

                        new_entities.extend(entities_list)

                        self.unregistered_keys[platform].pop(device_id)

            if new_entities:
                async_add_entities(new_entities)

        # End callback.

        # Add entities for keys seen for the first time.
        _add_entities_for_unregistered_keys()


@callback
def device_update_info(hass: HomeAssistant, rointe_device: RointeDevice) -> None:
    """Update device registry info."""

    LOGGER.debug("Updating device registry info for %s", rointe_device.name)

    dev_registry = device_registry.async_get(hass)

    if device := dev_registry.async_get_device(
        identifiers={(DOMAIN, rointe_device.id)},
    ):
        dev_registry.async_update_device(
            device.id, sw_version=rointe_device.firmware_version
        )
