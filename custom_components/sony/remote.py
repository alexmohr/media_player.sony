"""
Support for interface with a Sony Remote.

For more details about this platform, please refer to the documentation at
https://github.com/dilruacs/media_player.sony
"""
from __future__ import annotations

import logging
import time
from typing import Iterable, Any

from homeassistant.components.remote import (
    ATTR_DELAY_SECS,
    ATTR_HOLD_SECS,
    ATTR_NUM_REPEATS,
    DEFAULT_DELAY_SECS,
    DEFAULT_HOLD_SECS,
    DEFAULT_NUM_REPEATS,
    RemoteEntity,
    RemoteEntityFeature, ENTITY_ID_FORMAT)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_OFF, STATE_ON)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SonyCoordinator
from .const import DOMAIN, SONY_COORDINATOR, DEFAULT_DEVICE_NAME

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Use to setup entity."""
    _LOGGER.debug("Sony async_add_entities remote")
    coordinator = hass.data[DOMAIN][config_entry.entry_id][SONY_COORDINATOR]
    async_add_entities(
        [SonyRemoteEntity(coordinator)]
    )


# pylint: disable=unused-argument
# def setup_platform(hass, config, add_devices, discovery_info=None):
#     """Set up the Sony Remote platform."""
#     host = config.get(CONF_HOST)
#
#     if host is None:
#         return
#
#     pin = None
#     sony_config = load_json(hass.config.path(SONY_CONFIG_FILE))
#     logger = logging.getLogger('sonyapilib.device')
#     logger.setLevel(logging.CRITICAL)
#     while sony_config:
#         # Set up a configured TV
#         host_ip, host_config = sony_config.popitem()
#         if host_ip == host:
#             device = SonyDevice.load_from_json(host_config)
#             hass_device = SonyRemoteEntity(device)
#             add_devices([hass_device])
#             return
#
#     setup_sonyremote(config, pin, hass, add_devices)
#
#
# def setup_sonyremote(config, sony_device, hass, add_devices):
#     """Set up a Sony Media Player based on host parameter."""
#     host = config.get(CONF_HOST)
#     broadcast = config.get(CONF_BROADCAST_ADDRESS)
#
#     if sony_device is None:
#         request_configuration(config, hass, add_devices)
#     else:
#         # If we came here and configuring this host, mark as done
#         if host in _CONFIGURING:
#             request_id = _CONFIGURING.pop(host)
#             configurator = hass.components.configurator
#             configurator.request_done(request_id)
#             _LOGGER.info("Discovery configuration done")
#
#         if broadcast:
#             sony_device.broadcast = broadcast
#
#         hass_device = SonyRemoteEntity(sony_device)
#         config[host] = hass_device.sonydevice.save_to_json()
#
#         # Save config, we need the mac address to support wake on LAN
#         save_json(hass.config.path(SONY_CONFIG_FILE), config)
#
#         add_devices([hass_device])
#
#
# def request_configuration(config, hass, add_devices):
#     """Request configuration steps from the user."""
#     host = config.get(CONF_HOST)
#     name = config.get(CONF_NAME)
#     app_port = config.get(CONF_APP_PORT)
#     dmr_port = config.get(CONF_DMR_PORT)
#     ircc_port = config.get(CONF_IRCC_PORT)
#     psk = None
#
#     configurator = hass.components.configurator
#
#     # We got an error if this method is called while we are configuring
#     if host in _CONFIGURING:
#         configurator.notify_errors(
#             _CONFIGURING[host], "Failed to register, please try again.")
#         return
#
#     def sony_configuration_callback(data):
#         """Handle the entry of user PIN."""
#         from sonyapilib.device import AuthenticationResult
#
#         pin = data.get('pin')
#         sony_device = SonyDevice(host, name,
#                                  psk=psk, app_port=app_port,
#                                  dmr_port=dmr_port, ircc_port=ircc_port)
#
#         authenticated = False
#
#         # make sure we only send the authentication to the device
#         # if we have a valid pin
#         if pin == '0000' or pin is None or pin == '':
#             register_result = sony_device.register()
#             if register_result == AuthenticationResult.SUCCESS:
#                 authenticated = True
#             elif register_result == AuthenticationResult.PIN_NEEDED:
#                 # return so next call has the correct pin
#                 return
#             else:
#                 _LOGGER.error("An unknown error occured during registration")
#
#         authenticated = sony_device.send_authentication(pin)
#         if authenticated:
#             setup_sonyremote(config, sony_device, hass, add_devices)
#         else:
#             request_configuration(config, hass, add_devices)
#
#     _CONFIGURING[host] = configurator.request_config(
#         name, sony_configuration_callback,
#         description='Enter the Pin shown on your Sony Device. '
#         'If no Pin is shown, enter 0000 '
#         'to let the device show you a Pin.',
#         description_image="/static/images/smart-tv.png",
#         submit_caption="Confirm",
#         fields=[{'id': 'pin', 'name': 'Enter the pin', 'type': ''}]
#     )


class SonyRemoteEntity(CoordinatorEntity[SonyCoordinator], RemoteEntity):
    # pylint: disable=too-many-instance-attributes
    """Representation of a Sony mediaplayer."""
    _attr_supported_features = RemoteEntityFeature.ACTIVITY

    def __init__(self, coordinator):
        """
        Initialize the Sony remote device.

        Mac address is optional but neccessary for wake on LAN
        """
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._name = f"{DEFAULT_DEVICE_NAME} Remote"
        # self._attr_name = f"{self.coordinator.api.name} Remote"
        self._attr_icon = "mdi:remote-tv"
        self._attr_native_value = "OFF"
        self._state = STATE_OFF
        self._muted = False
        self._id = None
        self._playing = False
        self._unique_id = ENTITY_ID_FORMAT.format(
            f"{self.coordinator.api.host}_Remote")

        try:
            self.update()
        except Exception:  # pylint: disable=broad-except
            self._state = STATE_OFF

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Mac address is unique identifiers within a specific domain
                (DOMAIN, self.coordinator.api.mac)
            },
            name=self.coordinator.api.nickname,
            manufacturer="Sony",
            model=self.coordinator.api.client_id
        )

    @property
    def unique_id(self) -> str | None:
        return self._unique_id

    def update(self):
        """Update TV info."""
        _LOGGER.debug("Sony media player update %s", self.coordinator.data)
        self._state = self.coordinator.data.get("state", None)

    @property
    def name(self):
        """Return the name of the device."""
        return self.coordinator.api.nickname

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return self._attr_supported_features

    def turn_on(self):
        """Turn the media player on."""
        self.coordinator.api.power(True)

    def turn_off(self):
        """Turn off media player."""
        self.coordinator.api.power(False)

    def toggle(self, activity: str = None, **kwargs):
        """Toggle a device."""
        if self._state == STATE_ON:
            self.turn_off()
        else:
            self.turn_on()

    def send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send commands to one device."""
        num_repeats = kwargs.get(ATTR_NUM_REPEATS, DEFAULT_NUM_REPEATS)
        delay_secs = kwargs.get(ATTR_DELAY_SECS, DEFAULT_DELAY_SECS)
        hold_secs = kwargs.get(ATTR_HOLD_SECS, DEFAULT_HOLD_SECS)

        _LOGGER.debug("async_send_command %s %d repeats %d delay", ''.join(list(command)), num_repeats, delay_secs)

        for _ in range(num_repeats):
            for single_command in command:
                # Not supported : hold and release modes
                # if hold_secs > 0:
                #     self.sonydevice._send_command(single_command)
                #     time.sleep(hold_secs)
                # else:
                self.coordinator.api._send_command(single_command)
                time.sleep(delay_secs)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Update only if activity changed
        self.update()
        self.async_write_ha_state()
        return super()._handle_coordinator_update()