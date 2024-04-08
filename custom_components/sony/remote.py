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
    ATTR_NUM_REPEATS,
    DEFAULT_DELAY_SECS,
    DEFAULT_NUM_REPEATS,
    RemoteEntity,
    RemoteEntityFeature, ENTITY_ID_FORMAT
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SonyCoordinator
from .const import DOMAIN, SONY_COORDINATOR
from .helper import create_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Use to set up entity."""
    _LOGGER.debug("Sony async_add_entities remote")
    coordinator = hass.data[DOMAIN][config_entry.entry_id][SONY_COORDINATOR]

    async_add_entities(
        [SonyRemoteEntity(coordinator)]
    )


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

        self._attr_icon = "mdi:remote-tv"
        self._attr_native_value = "OFF"

        self._attr_state = STATE_OFF
        self._muted = False
        self._playing = False
        self._id = None

        self._unique_id = ENTITY_ID_FORMAT.format(
            f"{self.coordinator.api.host}_remote"
        )

        try:
            self.update()
        except Exception:  # pylint: disable=broad-except
            self._attr_state = STATE_OFF

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return create_device_info(self.coordinator.api, self.name)

    @property
    def name(self):
        """Return the name of the device."""
        return f"{self.coordinator.api.friendly_name}"  # Remote

    @property
    def unique_id(self) -> str | None:
        """Return the unique id of the device."""
        return self._unique_id

    def update(self):
        """Update TV info."""
        _LOGGER.debug("Sony media player update %s", self.coordinator.data)
        self._attr_state = self.coordinator.data.get("state", None)
        self._attr_is_on = self._attr_state != STATE_OFF

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

    # def toggle(self, activity: str = None, **kwargs):
    #    """Toggle a device."""
    #    if self._attr_state == STATE_ON:
    #        self.turn_off()
    #    else:
    #        self.turn_on()

    def send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send commands to one device."""
        num_repeats = kwargs.get(ATTR_NUM_REPEATS, DEFAULT_NUM_REPEATS)
        delay_secs = kwargs.get(ATTR_DELAY_SECS, DEFAULT_DELAY_SECS)
        # hold_secs = kwargs.get(ATTR_HOLD_SECS, DEFAULT_HOLD_SECS)

        _LOGGER.debug("async_send_command %s %d repeats %d delay",
                      ''.join(list(command)), num_repeats, delay_secs)

        for _ in range(num_repeats):
            for single_command in command:
                # TODO:
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
