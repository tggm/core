"""Number platform to configure preset temperatures."""
from __future__ import annotations

from abc import ABC

from rointesdk.device import RointeDevice

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import TEMP_CELSIUS, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CMD_SET_COMFORT_PRESET,
    CMD_SET_ECO_PRESET,
    CMD_SET_SCREEN_OPTIONS,
    DOMAIN,
    LOGGER,
    ROINTE_COORDINATOR,
)
from .coordinator import RointeDataUpdateCoordinator
from .rointe_entity import RointeRadiatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the radiator sensors from the config entry."""
    coordinator: RointeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        ROINTE_COORDINATOR
    ]

    # Hook a callback for discovered entities for the sensor entities.
    coordinator.add_entities_for_seen_keys(
        async_add_entities,
        [
            RointeEcoTemperature,
            RointeComfortTemperature,
            RointeStandbyBrightness,
            RointeScreenActiveBrightness,
        ],
        "number",
    )


class RointeComfortTemperature(RointeRadiatorEntity, NumberEntity, ABC):
    """Configuration for the ECO temperature preset."""

    def __init__(
        self, radiator: RointeDevice, coordinator: RointeDataUpdateCoordinator
    ) -> None:
        """Init the entity."""

        self._attr_native_min_value = 19
        self._attr_native_max_value = 30
        self._attr_native_step = 0.5
        self._attr_device_class = NumberDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

        description = NumberEntityDescription(
            key="comfort_temp_preset",
            name="Comfort Temp. Preset",
            native_unit_of_measurement=TEMP_CELSIUS,
            device_class=NumberDeviceClass.TEMPERATURE,
            entity_category=EntityCategory.CONFIG,
        )

        super().__init__(
            coordinator,
            radiator,
            name=f"{radiator.name} {description.name}",
            unique_id=f"{radiator.id}-{description.key}",
        )

        self.entity_description = description

    @property
    def icon(self) -> str | None:
        """Icon of the entity."""
        return "mdi:white-balance-sunny"

    @property
    def native_value(self) -> float | None:
        """Return the Comfort preset temperature."""
        return self._radiator.comfort_temp

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        LOGGER.debug("Setting Comfort temperature preset: %s", value)

        if not await self.device_manager.send_command(
            self._radiator, CMD_SET_COMFORT_PRESET, value
        ):
            LOGGER.error(
                "Failed to set Comfort preset temperature to [%s] for [%s]",
                value,
                self._radiator.name,
            )

            raise HomeAssistantError(
                f"Failed to set Comfort Temperature preset for {self._radiator.name}"
            )

        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()


class RointeEcoTemperature(RointeRadiatorEntity, NumberEntity, ABC):
    """Configuration for the ECO temperature preset."""

    def __init__(
        self, radiator: RointeDevice, coordinator: RointeDataUpdateCoordinator
    ) -> None:
        """Init the entity."""

        self._attr_native_min_value = 7.5
        self._attr_native_max_value = 18.5
        self._attr_native_step = 0.5
        self._attr_device_class = NumberDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

        description = NumberEntityDescription(
            key="eco_temp_preset",
            name="ECO Temp. Preset",
            native_unit_of_measurement=TEMP_CELSIUS,
            device_class=NumberDeviceClass.TEMPERATURE,
            entity_category=EntityCategory.CONFIG,
        )

        super().__init__(
            coordinator,
            radiator,
            name=f"{radiator.name} {description.name}",
            unique_id=f"{radiator.id}-{description.key}",
        )

        self.entity_description = description

    @property
    def icon(self) -> str | None:
        """Icon of the entity."""
        return "mdi:leaf"

    @property
    def native_value(self) -> float | None:
        """Return the ECO preset temperature."""
        return self._radiator.eco_temp

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        LOGGER.debug("Setting ECO temperature preset: %s", value)

        if not await self.device_manager.send_command(
            self._radiator, CMD_SET_ECO_PRESET, value
        ):
            LOGGER.error(
                "Failed to set Eco preset temperature to [%s] for [%s]",
                value,
                self._radiator.name,
            )

            raise HomeAssistantError(
                f"Failed to set ECO Temperature preset for {self._radiator.name}"
            )

        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()


class RointeScreenActiveBrightness(RointeRadiatorEntity, NumberEntity, ABC):
    """Configuration for the screen brightness."""

    def __init__(
        self, radiator: RointeDevice, coordinator: RointeDataUpdateCoordinator
    ) -> None:
        """Init the entity."""

        self._attr_native_min_value = 0
        self._attr_native_max_value = 10
        self._attr_native_step = 1

        description = NumberEntityDescription(
            key="screen_active_brightness",
            name="Screen Brightness",
            entity_category=EntityCategory.CONFIG,
        )

        super().__init__(
            coordinator,
            radiator,
            name=f"{radiator.name} {description.name}",
            unique_id=f"{radiator.id}-{description.key}",
        )

        self.entity_description = description

    @property
    def icon(self) -> str | None:
        """Icon of the entity."""
        return "mdi:brightness-7"

    @property
    def native_value(self) -> float | None:
        """Return the active screen brightness."""
        return self._radiator.brightness_on

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""

        # Optimist approach: Store the value and send the request to the device
        self._radiator.brightness_on = int(value)

        if not await self.device_manager.send_command(
            self._radiator, CMD_SET_SCREEN_OPTIONS
        ):
            LOGGER.error(
                "Failed to set screen options for [%s]",
                self._radiator.name,
            )

            raise HomeAssistantError(
                f"Failed to set screen options for {self._radiator.name}"
            )

        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()


class RointeStandbyBrightness(RointeRadiatorEntity, NumberEntity, ABC):
    """Configuration for the ECO temperature preset."""

    def __init__(
        self, radiator: RointeDevice, coordinator: RointeDataUpdateCoordinator
    ) -> None:
        """Init the entity."""

        self._attr_native_min_value = 0
        self._attr_native_max_value = 10
        self._attr_native_step = 1

        description = NumberEntityDescription(
            key="screen_standby_brightness",
            name="Standby Brightness",
            entity_category=EntityCategory.CONFIG,
        )

        super().__init__(
            coordinator,
            radiator,
            name=f"{radiator.name} {description.name}",
            unique_id=f"{radiator.id}-{description.key}",
        )

        self.entity_description = description

    @property
    def icon(self) -> str | None:
        """Icon of the entity."""
        return "mdi:brightness-3"

    @property
    def native_value(self) -> float | None:
        """Return the standby screen brightness."""
        return self._radiator.brightness_standby

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""

        # Optimist approach: Store the value and send the request to the device
        self._radiator.brightness_standby = int(value)

        if not await self.device_manager.send_command(
            self._radiator, CMD_SET_SCREEN_OPTIONS
        ):
            LOGGER.error(
                "Failed to set screen options for [%s]",
                self._radiator.name,
            )

            raise HomeAssistantError(
                f"Failed to set screen options for {self._radiator.name}"
            )

        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()
