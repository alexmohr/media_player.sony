"""
Support for interface with a Sony MediaPlayer TV.

For more details about this platform, please refer to the documentation at
https://github.com/dilruacs/media_player.sony
"""
import logging
import time

from sonyapilib.device import SonyDevice

import voluptuous as vol

from homeassistant.components.media_player import (
    MediaPlayerEntity, PLATFORM_SCHEMA)

from homeassistant.components.media_player.const import (
    SUPPORT_NEXT_TRACK, SUPPORT_PAUSE, SUPPORT_PREVIOUS_TRACK, SUPPORT_TURN_ON,
    SUPPORT_TURN_OFF, SUPPORT_PLAY, SUPPORT_PLAY_MEDIA, SUPPORT_STOP,
    SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_STEP, SUPPORT_VOLUME_SET)

from homeassistant.const import (
    CONF_HOST, CONF_NAME, STATE_OFF, STATE_ON, STATE_PLAYING, STATE_PAUSED)
import homeassistant.helpers.config_validation as cv

from homeassistant.util.json import load_json, save_json


VERSION = '0.1.3'

REQUIREMENTS = ['sonyapilib==0.4.3']

SONY_CONFIG_FILE = 'sony.conf'

CLIENTID_PREFIX = 'HomeAssistant'

DEFAULT_NAME = 'Sony Media Player'

NICKNAME = 'Home Assistant'

CONF_BROADCAST_ADDRESS = 'broadcast_address'
CONF_APP_PORT = 'app_port'
CONF_DMR_PORT = 'dmr_port'
CONF_IRCC_PORT = 'ircc_port'
DEFAULT_APP_PORT = 50202
DEFAULT_DMR_PORT = 52323
DEFAULT_IRCC_PORT = 50001


# Map ip to request id for configuring
_CONFIGURING = {}

_LOGGER = logging.getLogger(__name__)

SUPPORT_SONY = SUPPORT_PAUSE | \
    SUPPORT_PREVIOUS_TRACK | SUPPORT_NEXT_TRACK | \
    SUPPORT_TURN_ON | SUPPORT_TURN_OFF | \
    SUPPORT_PLAY | SUPPORT_PLAY_MEDIA | SUPPORT_STOP | \
    SUPPORT_VOLUME_MUTE | SUPPORT_VOLUME_STEP | SUPPORT_VOLUME_SET

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_BROADCAST_ADDRESS): cv.string,
    vol.Optional(CONF_APP_PORT, default=DEFAULT_APP_PORT): cv.port,
    vol.Optional(CONF_DMR_PORT, default=DEFAULT_DMR_PORT): cv.port,
    vol.Optional(CONF_IRCC_PORT, default=DEFAULT_IRCC_PORT): cv.port
})


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Sony Media Player platform."""
    host = config.get(CONF_HOST)

    if host is None:
        return

    pin = None
    sony_config = load_json(hass.config.path(SONY_CONFIG_FILE))

    while sony_config:
        # Set up a configured TV
        host_ip, host_config = sony_config.popitem()
        if host_ip == host:
            device = SonyDevice.load_from_json(host_config)
            hass_device = SonyMediaPlayerEntity(device)
            add_devices([hass_device])
            return

    setup_sonymediaplayer(config, pin, hass, add_devices)


def setup_sonymediaplayer(config, sony_device, hass, add_devices):
    """Set up a Sony Media Player based on host parameter."""
    host = config.get(CONF_HOST)
    broadcast = config.get(CONF_BROADCAST_ADDRESS)

    if sony_device is None:
        request_configuration(config, hass, add_devices)
    else:
        # If we came here and configuring this host, mark as done
        if host in _CONFIGURING:
            request_id = _CONFIGURING.pop(host)
            configurator = hass.components.configurator
            configurator.request_done(request_id)
            _LOGGER.info("Discovery configuration done")

        if broadcast:
            sony_device.broadcast = broadcast

        hass_device = SonyMediaPlayerEntity(sony_device)
        config[host] = hass_device.sonydevice.save_to_json()

        # Save config, we need the mac address to support wake on LAN
        save_json(hass.config.path(SONY_CONFIG_FILE), config)

        add_devices([hass_device])


def request_configuration(config, hass, add_devices):
    """Request configuration steps from the user."""
    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)
    app_port = config.get(CONF_APP_PORT)
    dmr_port = config.get(CONF_DMR_PORT)
    ircc_port = config.get(CONF_IRCC_PORT)
    psk = None

    configurator = hass.components.configurator

    # We got an error if this method is called while we are configuring
    if host in _CONFIGURING:
        configurator.notify_errors(
            _CONFIGURING[host], "Failed to register, please try again.")
        return

    def sony_configuration_callback(data):
        """Handle the entry of user PIN."""
        from sonyapilib.device import AuthenticationResult

        pin = data.get('pin')
        sony_device = SonyDevice(host, name,
                                 psk=psk, app_port=app_port,
                                 dmr_port=dmr_port, ircc_port=ircc_port)

        authenticated = False

        # make sure we only send the authentication to the device
        # if we have a valid pin
        if pin == '0000' or pin is None or pin == '':
            register_result = sony_device.register()
            if register_result == AuthenticationResult.SUCCESS:
                authenticated = True
            elif register_result == AuthenticationResult.PIN_NEEDED:
                # return so next call has the correct pin
                return
            else:
                _LOGGER.error("An unknown error occured during registration")

        authenticated = sony_device.send_authentication(pin)
        if authenticated:
            setup_sonymediaplayer(config, sony_device, hass, add_devices)
        else:
            request_configuration(config, hass, add_devices)

    _CONFIGURING[host] = configurator.request_config(
        name, sony_configuration_callback,
        description='Enter the Pin shown on your Sony Device. '
        'If no Pin is shown, enter 0000 '
        'to let the device show you a Pin.',
        description_image="/static/images/smart-tv.png",
        submit_caption="Confirm",
        fields=[{'id': 'pin', 'name': 'Enter the pin', 'type': ''}]
    )


class SonyMediaPlayerEntity(MediaPlayerEntity):
    # pylint: disable=too-many-instance-attributes
    """Representation of a Sony mediaplayer."""

    def __init__(self, sony_device):
        """
        Initialize the Sony mediaplayer device.

        Mac address is optional but neccessary for wake on LAN
        """
        self.sonydevice = sony_device
        self._state = STATE_OFF
        self._attr_volume_level = 0
        self._muted = False
        self._id = None
        self._playing = False
        _LOGGER.error(sony_device.pin)
        _LOGGER.error(sony_device.client_id)

        try:
            self.update()
        except Exception:  # pylint: disable=broad-except
            self._state = STATE_OFF

    def update(self):
        """Update TV info."""
        self.sonydevice.init_device()
        if not self.sonydevice.get_power_status():
            self._state = STATE_OFF
            return

        self._state = STATE_ON

        # Retrieve the latest data.
        try:
            if self._state == STATE_ON:
                power_status = self.sonydevice.get_power_status()
                if power_status:
                    self.update_volume()
                    playback_info = self.sonydevice.get_playing_status()
                    if playback_info == "PLAYING":
                        self._state = STATE_PLAYING
                    elif playback_info == "PAUSED_PLAYBACK":
                        self._state = STATE_PAUSED
                    else:
                        self._state = STATE_ON
                else:
                    self._state = STATE_OFF

        except Exception as exception_instance:  # pylint: disable=broad-except
            _LOGGER.error(exception_instance)
            self._state = STATE_OFF

    def update_volume(self):
        """Update volume info."""
        self._attr_volume_level = self.sonydevice.get_volume() / 100
        _LOGGER.debug(self._attr_volume_level)

    @property
    def name(self):
        """Return the name of the device."""
        return self.sonydevice.nickname

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
        self.sonydevice.power(True)

    def turn_off(self):
        """Turn off media player."""
        self.sonydevice.power(False)

    def media_play_pause(self):
        """Simulate play pause media player."""
        if self._playing:
            self.media_pause()
        else:
            self.media_play()

    def media_play(self):
        """Send play command."""
        _LOGGER.debug(self.sonydevice.commands)
        self._playing = True
        self.sonydevice.play()

    def media_pause(self):
        """Send media pause command to media player."""
        self._playing = False
        self.sonydevice.pause()

    def media_next_track(self):
        """Send next track command."""
        self.sonydevice.next()

    def media_previous_track(self):
        """Send the previous track command."""
        self.sonydevice.prev()

    def media_stop(self):
        """Send stop command."""
        self.sonydevice.stop()

    def volume_up(self):
        """Send stop command."""
        self.sonydevice.volume_up()
        time.sleep(0.5)
        self.update_volume()

    def volume_down(self):
        """Send stop command."""
        self.sonydevice.volume_down()
        time.sleep(0.5)
        self.update_volume()

    def set_volume_level(self, volume):
        """Send set volume command."""
        self.sonydevice.set_volume(int(volume * 100))

    def mute_volume(self, mute):
        """Send stop command."""
        self.sonydevice.mute()
