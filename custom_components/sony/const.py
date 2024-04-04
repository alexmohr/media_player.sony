"""Constants for the Sony integration."""
from datetime import timedelta

DOMAIN = "sony"

CONF_NAME = "sony"
DEVICE_SCAN_INTERVAL = timedelta(seconds=60)
SONY_COORDINATOR = "sony_coordinator"
SONY_API = "sony_api"
DEFAULT_DEVICE_NAME = "Sony Device"

CONF_HOST = "host"
CONF_PIN = "pin"
CONF_APP_PORT = 'app_port'
CONF_DMR_PORT = 'dmr_port'
CONF_IRCC_PORT = 'ircc_port'

DEFAULT_APP_PORT = 50202
DEFAULT_DMR_PORT = 52323
DEFAULT_IRCC_PORT = 50001