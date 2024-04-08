"""Helper functions."""
from sonyapilib.device import SonyDevice
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN


def create_device_info(device: SonyDevice, name: str) -> DeviceInfo:
    """Create device info based on device api and device name."""
    return DeviceInfo(
        identifiers={
            # Mac address is unique identifiers within a specific domain
            (DOMAIN, device.mac)
        },
        name=name,
        manufacturer=device.manufacturer,
        model=device.model_name
    )
