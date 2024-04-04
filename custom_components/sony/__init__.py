"""The sony component."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from sonyapilib.device import SonyDevice, AuthenticationResult

from .const import (DOMAIN,
                    CONF_NAME, CONF_HOST, CONF_PIN, CONF_MAC_ADDRESS, CONF_BROADCAST_ADDRESS, CONF_APP_PORT, CONF_IRCC_PORT, CONF_DMR_PORT,
                    SONY_COORDINATOR, SONY_API, DEFAULT_DEVICE_NAME, SONY_DEFAULT_DEVICE_NAME)
from .coordinator import SonyCoordinator

_LOGGER: logging.Logger = logging.getLogger(__package__)

PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
    Platform.REMOTE
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Unfolded Circle Remote from a config entry."""

    try:
        sony_device = SonyDevice(entry.data[CONF_HOST], SONY_DEFAULT_DEVICE_NAME,
                                 psk=None, app_port=entry.data[CONF_APP_PORT],
                                 dmr_port=entry.data[CONF_DMR_PORT], ircc_port=entry.data[CONF_IRCC_PORT])
        pin = entry.data.get(CONF_PIN, None)
        sony_device.pin = pin
        sony_device.mac = entry.data.get(CONF_MAC_ADDRESS, None)
        sony_device.broadcast = entry.data.get(CONF_BROADCAST_ADDRESS, None)

        if pin is None or pin == '0000' or pin is None or pin == '':
            register_result = await hass.async_add_executor_job(sony_device.register)
            if register_result == AuthenticationResult.PIN_NEEDED:
                raise ConfigEntryAuthFailed(Exception("Authentication error"))
            # entry.async_create_task(sony_device.init_device())
        else:
            pass
            # entry.async_create_task(sony_device.init_device())
            # hass.async_create_task(sony_device.init_device())
            # await hass.async_add_executor_job(sony_device.init_device)
            # authenticated = await hass.async_add_executor_job(sony_device.send_authentication, pin)
            # if not authenticated:
            #     raise ConfigEntryAuthFailed(Exception("Authentication error"))
    except Exception as ex:
        raise ConfigEntryNotReady(ex) from ex

    _LOGGER.debug("Sony device initialization %s", vars(sony_device))
    coordinator = SonyCoordinator(hass, sony_device)
    # hass.async_create_task(coordinator.api.init_device())
    # await hass.async_add_executor_job(coordinator.api.init_device)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        SONY_COORDINATOR: coordinator,
        SONY_API: sony_device,
    }

    logging.getLogger("sonyapilib").setLevel(logging.CRITICAL)

    # Retrieve info from Remote
    # Get Basic Device Information
    await coordinator.async_config_entry_first_refresh()

    # Extract activities and activity groups
    # await coordinator.api.update()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))
    # TODO Sony device supports SSDP discovery
    # await zeroconf.async_get_async_instance(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        pass
        # coordinator: SonyCoordinator = hass.data[DOMAIN][entry.entry_id][SONY_COORDINATOR]
        # coordinator.api.?
    except Exception as ex:
        _LOGGER.error("Sony device async_unload_entry error", ex)
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Update Listener."""
    # TODO Should be ?
    # await async_unload_entry(hass, entry)
    # await async_setup_entry(hass, entry)
    await hass.config_entries.async_reload(entry.entry_id)
