"""The sony component."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady
)
from sonyapilib.device import SonyDevice, AuthenticationResult

from .const import (DOMAIN,
                    CONF_HOST, CONF_PIN,
                    CONF_MAC_ADDRESS, CONF_BROADCAST_ADDRESS,
                    CONF_APP_PORT, CONF_IRCC_PORT, CONF_DMR_PORT,
                    CONF_UPDATE_INTERVAL,
                    SONY_COORDINATOR, SONY_API,
                    DEFAULT_PIN,
                    DEFAULT_BROADCAST_ADDRESS,
                    DEFAULT_UPDATE_INTERVAL,
                    DEFAULT_DEVICE_NAME)
from .coordinator import SonyCoordinator

_LOGGER: logging.Logger = logging.getLogger(__package__)

PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
    Platform.REMOTE
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Unfolded Circle Remote from a config entry."""
    try:
        broadcast_address = entry.data.get(
            CONF_BROADCAST_ADDRESS,
            DEFAULT_BROADCAST_ADDRESS
        )

        sony_device = SonyDevice(entry.data[CONF_HOST], DEFAULT_DEVICE_NAME,
                                 broadcast_address=broadcast_address,
                                 app_port=entry.data[CONF_APP_PORT],
                                 dmr_port=entry.data[CONF_DMR_PORT],
                                 ircc_port=entry.data[CONF_IRCC_PORT])

        pin = entry.data.get(CONF_PIN, DEFAULT_PIN)
        sony_device.pin = pin
        sony_device.mac = entry.data.get(CONF_MAC_ADDRESS, None)
        sony_device.broadcast = entry.data.get(
            CONF_BROADCAST_ADDRESS,
            DEFAULT_BROADCAST_ADDRESS
        )

        if not pin or pin == DEFAULT_PIN:
            register_result = await hass.async_add_executor_job(
                sony_device.register
            )

            if register_result == AuthenticationResult.PIN_NEEDED:
                raise ConfigEntryAuthFailed(Exception("Authentication error"))
        else:
            pass

            # TODO:
            # entry.async_create_task(sony_device.init_device())
            # hass.async_create_task(sony_device.init_device())
            # await hass.async_add_executor_job(sony_device.init_device)
            # authenticated = await hass.async_add_executor_job(
            #     sony_device.send_authentication, pin
            # )
            # if not authenticated:
            #     raise ConfigEntryAuthFailed(
            #         Exception("Authentication error")
            #     )
    except Exception as ex:
        raise ConfigEntryNotReady(ex) from ex

    friendly_name = entry.data.get(
        CONF_NAME,
        sony_device.friendly_name
    )

    update_interval = entry.data.get(
        CONF_UPDATE_INTERVAL,
        DEFAULT_UPDATE_INTERVAL
    )

    _LOGGER.debug("Sony device initialization %s", vars(sony_device))
    coordinator = SonyCoordinator(hass, sony_device,
                                  friendly_name=friendly_name,
                                  update_interval=update_interval)

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

    # TODO: Sony device supports SSDP discovery
    # await zeroconf.async_get_async_instance(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        pass

        # TODO:
        # coordinator: SonyCoordinator = \
        # hass.data[DOMAIN][entry.entry_id][SONY_COORDINATOR]
        # coordinator.api.?
    except Exception as ex:
        _LOGGER.error("Sony device async_unload_entry error", ex)

    if unload_ok := await hass.config_entries.async_unload_platforms(
            entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Update Listener."""
    # TODO: Should be ?
    # await async_unload_entry(hass, entry)
    # await async_setup_entry(hass, entry)

    await hass.config_entries.async_reload(entry.entry_id)
