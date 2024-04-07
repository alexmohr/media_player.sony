"""
Support for interface with a Sony MediaPlayer TV.

For more details about this platform, please refer to the documentation at
https://github.com/dilruacs/media_player.sony
"""
import logging

from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerDeviceClass, ENTITY_ID_FORMAT
from homeassistant.components.media_player.const import (
    MediaPlayerEntityFeature)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SonyCoordinator
from .const import DOMAIN, SONY_COORDINATOR

_LOGGER = logging.getLogger(__name__)

SUPPORT_SONY = (MediaPlayerEntityFeature.VOLUME_MUTE | MediaPlayerEntityFeature.VOLUME_STEP |
                MediaPlayerEntityFeature.PREVIOUS_TRACK | MediaPlayerEntityFeature.NEXT_TRACK |
                MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF |
                MediaPlayerEntityFeature.PLAY | MediaPlayerEntityFeature.PLAY_MEDIA | MediaPlayerEntityFeature.PAUSE | MediaPlayerEntityFeature.STOP)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Use to set up entity."""
    _LOGGER.debug("Sony async_add_entities media player")
    coordinator = hass.data[DOMAIN][config_entry.entry_id][SONY_COORDINATOR]
    async_add_entities(
        [SonyMediaPlayerEntity(coordinator)]
    )


class SonyMediaPlayerEntity(CoordinatorEntity[SonyCoordinator], MediaPlayerEntity):
    # pylint: disable=too-many-instance-attributes
    """Representation of a Sony mediaplayer."""

    def __init__(self, coordinator):
        """
        Initialize the Sony mediaplayer device.

        Mac address is optional but necessary for wake on LAN
        """
        super().__init__(coordinator)
        self.coordinator = coordinator
        # self._name = f"{self.coordinator.api.name} Media Player"
        # self._attr_name = f"{self.coordinator.api.name} Media Player"
        self._state = STATE_OFF
        self._attr_volume_level = 0
        self._attr_is_volume_muted = False
        self._id = None
        self._playing = False

        self._unique_id = ENTITY_ID_FORMAT.format(
            f"{self.coordinator.api.host}_media_player")

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
            name=self.coordinator.api.friendly_name,
            manufacturer=self.coordinator.api.manufacturer,
            model=self.coordinator.api.model_name
        )

    @property
    def unique_id(self) -> str | None:
        return self._unique_id

    @property
    def device_class(self) -> MediaPlayerDeviceClass | None:
        return MediaPlayerDeviceClass.RECEIVER  # TODO: Maybe something else in some cases?

    def update(self):
        """Update TV info."""
        _LOGGER.debug("Sony media player update %s", self.coordinator.data)
        self._state = self.coordinator.data.get("state", None)
        self.update_volume()

    def update_volume(self):
        """Update volume level info."""
        self._attr_volume_level = self.coordinator.data.get("volume", 0)
        self._attr_is_volume_muted = self.coordinator.data.get("muted", False)  # TODO: Update
        _LOGGER.debug(self._attr_volume_level)

    @property
    def name(self):
        """Return the name of the device."""
        return self.coordinator.api.friendly_name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_SONY

    @property
    def media_title(self):
        """Title of current playing media."""
        # the device used for testing does not send any
        # information about the media which is played
        return ""

    @property
    def media_content_id(self):
        """Content ID of current playing media."""
        return ""

    @property
    def media_duration(self):
        """Duration of current playing media in seconds."""
        return ""

    def turn_on(self):
        """Turn the media player on."""
        self.coordinator.api.power(True)

    def turn_off(self):
        """Turn off media player."""
        self.coordinator.api.power(False)

    def media_play_pause(self):
        """Simulate play pause media player."""
        if self._playing:
            self.media_pause()
        else:
            self.media_play()

    def media_play(self):
        """Send play command."""
        _LOGGER.debug(self.coordinator.api.commands)
        self._playing = True
        self.coordinator.api.play()

    def media_pause(self):
        """Send media pause command to media player."""
        self._playing = False
        self.coordinator.api.pause()

    def media_next_track(self):
        """Send next track command."""
        self.coordinator.api.next()

    def media_previous_track(self):
        """Send the previous track command."""
        self.coordinator.api.prev()

    def media_stop(self):
        """Send stop command."""
        self.coordinator.api.stop()

    def volume_up(self):
        """Send stop command."""
        self.coordinator.api.volume_up()
        # TODO: Update volume
        # time.sleep(0.5)
        # self.update_volume()

    def volume_down(self):
        """Send stop command."""
        self.coordinator.api.volume_down()
        # TODO: Update volume
        # time.sleep(0.5)
        # self.update_volume()

    def mute_volume(self, mute):
        """Send stop command."""
        self.coordinator.api.mute()
        # TODO: Update volume

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Update only if activity changed
        self.update()
        self.async_write_ha_state()

        return super()._handle_coordinator_update()
