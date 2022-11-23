"""Support for Rointe Climate."""

from __future__ import annotations

from datetime import timedelta
import logging

from rointesdk.device import RointeDevice

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    CURRENT_HVAC_OFF,
    HVAC_MODE_AUTO,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_COMFORT,
    PRESET_ECO,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CMD_SET_HVAC_MODE,
    CMD_SET_PRESET,
    CMD_SET_TEMP,
    DOMAIN,
    PRESET_ROINTE_ICE,
    ROINTE_COORDINATOR,
    SCAN_INTERVAL_SECONDS,
)
from .coordinator import RointeDataUpdateCoordinator
from .rointe_entity import RointeRadiatorEntity

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(SCAN_INTERVAL_SECONDS)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Initialize all the rointe heaters found via API."""
    coordinator: RointeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        ROINTE_COORDINATOR
    ]

    # Hook a callback for discovered entities, for RointeHaClimate entities.
    coordinator.add_entities_for_seen_keys(
        async_add_entities, [RointeHaClimate], "climate"
    )


class RointeHaClimate(RointeRadiatorEntity, ClimateEntity):
    """Rointe radiator device."""

    def __init__(
        self,
        radiator: RointeDevice,
        coordinator: RointeDataUpdateCoordinator,
    ) -> None:
        """Initialize coordinator and Rointe super class."""

        super().__init__(
            coordinator, radiator, name=radiator.name, unique_id=radiator.id
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._radiator and self._radiator.hass_available

    @property
    def temperature_unit(self) -> str:
        """Temperature unit."""
        return TEMP_CELSIUS

    @property
    def target_temperature(self) -> float:
        """Return the current temperature."""
        if self._radiator.mode == "auto":
            if self._radiator.preset == "eco":
                return self._radiator.eco_temp
            elif self._radiator.preset == "comfort":
                return self._radiator.comfort_temp
            elif self._radiator.preset == "ice":
                return self._radiator.ice_temp

        return self._radiator.temp

    @property
    def current_temperature(self) -> float:
        """Get current temperature (Probe)."""
        return self._radiator.temp_probe

    @property
    def max_temp(self) -> float:
        """Max selectable temperature."""
        if self._radiator.user_mode_supported and self._radiator.user_mode:
            return self._radiator.um_max_temp

        return 30.0

    @property
    def min_temp(self) -> float:
        """Minimum selectable temperature."""
        if self._radiator.user_mode_supported and self._radiator.user_mode:
            return self._radiator.um_min_temp

        return 7.0

    @property
    def target_temperature_high(self) -> float:
        """Max selectable target temperature."""
        if self._radiator.user_mode_supported and self._radiator.user_mode:
            return self._radiator.um_max_temp

        return 30.0

    @property
    def target_temperature_low(self) -> float:
        """Minimum selectable target temperature."""
        if self._radiator.user_mode_supported and self._radiator.user_mode:
            return self._radiator.um_min_temp

        return 7.0

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE

    @property
    def target_temperature_step(self) -> float | None:
        """Temperature step."""
        return 0.5

    @property
    def hvac_modes(self) -> list[str]:
        """Return hvac modes available."""
        return [HVAC_MODE_OFF, HVAC_MODE_HEAT, HVAC_MODE_AUTO]

    @property
    def preset_modes(self) -> list[str]:
        """Return the available preset modes."""
        return [PRESET_COMFORT, PRESET_ECO, PRESET_ROINTE_ICE]

    @property
    def hvac_mode(self) -> str:
        """Return the current HVAC mode."""
        if not self._radiator.power:
            return HVAC_MODE_OFF

        if self._radiator.mode == "auto":
            return HVAC_MODE_AUTO
        else:
            return HVAC_MODE_HEAT

    @property
    def hvac_action(self) -> str:
        """Return the current HVAC action."""

        # Special mode for AUTO mode and waiting for schedule to activate.
        if self._radiator.mode == "auto" and self._radiator.preset == "off":
            return CURRENT_HVAC_IDLE

        # Forced to off, either on Manual or Auto mode.
        if not self._radiator.power:
            return CURRENT_HVAC_OFF

        # Otherwise, it's heating.
        return CURRENT_HVAC_HEAT

    @property
    def preset_mode(self) -> str | None:
        """Convert the device's preset to HA preset modes."""

        if self._radiator.preset == "eco":
            return PRESET_ECO
        elif self._radiator.preset == "comfort":
            return PRESET_COMFORT
        elif self._radiator.preset == "ice":
            return PRESET_ROINTE_ICE
        else:
            # Also captures "none" (man mode, temperature outside presets)
            return None

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        target_temperature = float(kwargs["temperature"])

        if not await self.get_device_manager().send_command(
            self._radiator, CMD_SET_TEMP, target_temperature
        ):
            _LOGGER.error(
                "Failed to set Temperature [%s] for [%s]",
                target_temperature,
                self._radiator.name,
            )

        await self._signal_thermostat_update()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""

        _LOGGER.info("Setting HVAC mode to %s", hvac_mode)

        if not await self.get_device_manager().send_command(
            self._radiator, CMD_SET_HVAC_MODE, hvac_mode
        ):
            _LOGGER.error(
                "Failed to set HVAC mode [%s] for [%s]", hvac_mode, self._radiator.name
            )

        await self._signal_thermostat_update()

    async def async_set_preset_mode(self, preset_mode):
        """Set new target preset mode."""
        _LOGGER.info("Setting preset mode: %s", preset_mode)

        if not await self.get_device_manager().send_command(
            self._radiator, CMD_SET_PRESET, preset_mode
        ):
            _LOGGER.error(
                "Failed to set preset mode [%s] for [%s]",
                preset_mode,
                self._radiator.name,
            )

        await self._signal_thermostat_update()

    async def _signal_thermostat_update(self):
        """Signal a radiator change."""

        # Update the data
        _LOGGER.debug("_signal_thermostat_update")
        await self.coordinator.async_request_refresh()
        _LOGGER.info("writing HA state")
        self.async_write_ha_state()
