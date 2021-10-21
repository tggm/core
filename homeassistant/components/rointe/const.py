"""Constants for the Rointe Heaters integration."""

import logging

from homeassistant.backports.enum import StrEnum
from homeassistant.const import Platform

LOGGER = logging.getLogger(__package__)

DOMAIN = "rointe"
DEVICE_DOMAIN = "climate"
PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SENSOR, Platform.UPDATE]
CONF_USERNAME = "rointe_username"
CONF_PASSWORD = "rointe_password"
CONF_INSTALLATION = "rointe_installation"

ROINTE_MANUFACTURER = "Rointe"

ROINTE_SUPPORTED_DEVICES = ["radiator", "towel", "therm", "radiatorb"]

RADIATOR_DEFAULT_TEMPERATURE = 20

PRESET_ROINTE_ICE = "ice"

RADIATOR_TEMP_STEP = 0.5
RADIATOR_TEMP_MIN = 7.0
RADIATOR_TEMP_MAX = 30.0


class RointePreset(StrEnum):
    """Rointe radiators preset modes."""

    ECO = "eco"
    COMFORT = "comfort"
    ICE = "ice"
    NONE = "none"


class RointeCommand(StrEnum):
    """Device commands."""

    SET_TEMP = "cmd_set_temp"
    SET_PRESET = "cmd_set_preset"
    SET_HVAC_MODE = "cmd_set_hvac_mode"


class RointeOperationMode(StrEnum):
    """Device operation mode."""

    AUTO = "auto"
    MANUAL = "manual"
