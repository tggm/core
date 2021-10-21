"""The Rointe Heaters integration."""
from __future__ import annotations

from rointesdk.rointe_api import ApiResponse, RointeAPI

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_INSTALLATION,
    CONF_LOCAL_ID,
    CONF_PASSWORD,
    CONF_USERNAME,
    DOMAIN,
    LOGGER,
    PLATFORMS,
    ROINTE_API_MANAGER,
    ROINTE_COORDINATOR,
    ROINTE_DEVICE_MANAGER,
    ROINTE_HA_DEVICES,
    ROINTE_HA_ROINTE_MAP,
)
from .coordinator import RointeDataUpdateCoordinator
from .device_manager import RointeDeviceManager


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Rointe Heaters from a config entry."""

    try:
        (
            rointe_device_manager,
            rointe_api,
            rointe_coordinator,
        ) = await init_device_manager(hass, entry)
    except ConfigEntryNotReady as ex:
        LOGGER.error(
            "An error occurred while setting up the Rointe Integration: %s", ex
        )
        raise
    else:
        # Initialize Hass data if necessary.
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
            ROINTE_HA_ROINTE_MAP: {},
            ROINTE_HA_DEVICES: set(),
        }

        hass.data[DOMAIN][entry.entry_id][ROINTE_DEVICE_MANAGER] = rointe_device_manager
        hass.data[DOMAIN][entry.entry_id][ROINTE_API_MANAGER] = rointe_api
        hass.data[DOMAIN][entry.entry_id][ROINTE_COORDINATOR] = rointe_coordinator

        return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and removes event handlers."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        rointe_data = hass.data[DOMAIN].pop(entry.entry_id)

        while rointe_data[ROINTE_COORDINATOR].cleanup_callbacks:
            rointe_data[ROINTE_COORDINATOR].cleanup_callbacks.pop()()

    return unload_ok


async def init_device_manager(
    hass: HomeAssistant, entry: ConfigEntry
) -> tuple[RointeDeviceManager, RointeAPI, RointeDataUpdateCoordinator]:
    """Initialize the device manager, API and coordinator."""

    rointe_api = RointeAPI(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])

    LOGGER.debug("Device manager: Logging in")

    # Login to the Rointe API.
    login_result: ApiResponse = await hass.async_add_executor_job(
        rointe_api.initialize_authentication
    )

    if not login_result.success:
        raise ConfigEntryNotReady("Unable to connect to the Rointe API")

    rointe_device_manager = RointeDeviceManager(
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        installation_id=entry.data[CONF_INSTALLATION],
        local_id=entry.data[CONF_LOCAL_ID],
        hass=hass,
        rointe_api=rointe_api,
    )

    LOGGER.debug("Device manager: Initializing Data Coordinator")
    rointe_coordinator = RointeDataUpdateCoordinator(hass, rointe_device_manager)

    LOGGER.debug("Device manager: Calling first refresh")
    await rointe_coordinator.async_config_entry_first_refresh()

    LOGGER.debug("Device manager: Setting up platforms")
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return rointe_device_manager, rointe_api, rointe_coordinator
