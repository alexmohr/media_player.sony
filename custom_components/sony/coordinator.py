"""The IntelliFire integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.error import HTTPError

import requests
from homeassistant.const import STATE_OFF, STATE_ON, STATE_PLAYING, STATE_PAUSED
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from sonyapilib.device import SonyDevice, HttpMethod

from .const import DEVICE_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SonyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Data update coordinator for an Unfolded Circle Remote device."""
    # List of events to subscribe to the websocket
    subscribe_events: dict[str, bool]

    def __init__(self, hass: HomeAssistant, sony_device) -> None:
        """Initialize the Coordinator."""
        super().__init__(
            hass,
            name=DOMAIN,
            logger=_LOGGER,
            update_interval=DEVICE_SCAN_INTERVAL,
        )
        self.hass = hass
        self.api: SonyDevice = sony_device
        self.device_data = SonyDeviceData(self)
        self.data = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Get the latest data from the Unfolded Circle Remote."""
        _LOGGER.debug("Sony device coordinator update")
        try:
            await self.device_data.update_state()
            # self.device_data.update_state()
            self.data = vars(self.api)
            self.data.update(vars(self.device_data))
            return self.data
        except Exception as ex:
            _LOGGER.error("Sony device coordinator error during update", ex)
            raise UpdateFailed(
                f"Error communicating with Sony device API {ex}"
            ) from ex


class SonyDeviceData:
    def __init__(self, coordinator: SonyCoordinator):
        self.coordinator = coordinator
        self.state = STATE_OFF
        self.volume = 0
        self._init = False

    async def init_device(self):
        """Initialize the device by reading the necessary resources from it."""
        sony_device = self.coordinator.api
        try:
            response = await self.coordinator.hass.async_add_executor_job(sony_device._send_http,sony_device.dmr_url, HttpMethod.GET)
        except requests.exceptions.ConnectionError:
            _LOGGER.debug("Sony device connection error, waiting next call")
            response = None
        except requests.exceptions.RequestException as exc:
            _LOGGER.error("Failed to get DMR: %s: %s", type(exc), exc)
            return

        try:
            if response:
                _LOGGER.debug("Sony device connection ready, proceed to init device")
                # sony_device._parse_dmr(response.text)
                await self.coordinator.hass.async_add_executor_job(sony_device.init_device)
                self._init = True
            else:
                _LOGGER.debug("Sony device connection not ready, wait next call")
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.error("Failed to get device information: %s, wait next call", str(ex))

    async def update_state(self) -> None:
        """Update TV info."""
        if not self._init:
            await self.init_device()
            if not self._init:
                return

        # response = await self.coordinator.hass.async_add_executor_job(self.coordinator.api._send_http,
        #                                              self.coordinator.api._get_action(
        #                                                  "getSystemInformation").url, HttpMethod.GET)
        # if response:
        #     _LOGGER.debug("Sony dump system information %s", response.text)

        _LOGGER.debug("Sony device SonyDeviceData update_state")
        power_status = await self.coordinator.hass.async_add_executor_job(self.coordinator.api.get_power_status)
        if not power_status:
            self.state = STATE_OFF
            self._init = False
            return

        self.state = STATE_ON
        await self.update_volume()

        # Retrieve the latest data.
        try:
            playback_info = await self.coordinator.hass.async_add_executor_job(self.coordinator.api.get_playing_status)
            if playback_info == "PLAYING":
                self.state = STATE_PLAYING
            elif playback_info == "PAUSED_PLAYBACK":
                self.state = STATE_PAUSED
            else:
                self.state = STATE_ON

        except Exception as exception_instance:  # pylint: disable=broad-except
            _LOGGER.error("Sony device error", exception_instance)
            self.state = STATE_OFF
            self._init = False

    async def update_volume(self) -> None:
        self.volume = await self.coordinator.hass.async_add_executor_job(self.coordinator.api.get_volume)
        _LOGGER.debug(self.volume)
