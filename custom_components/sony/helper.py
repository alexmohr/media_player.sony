"""Helper functions."""
from __future__ import annotations

import socket
import re
from enum import Enum

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


def validate_ip_address(address: str) -> bool:
    try:
        socket.inet_aton(address)
        return True
    except socket.error:
        return False


def validate_mac_address(address: str) -> bool:
    if re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", address.lower()):
        return True

    return False


class ValidationResult(Enum):
    SUCCESS = "success"
    INVALID_HOST = "invalid_host"
    INVALID_BROADCAST_ADDRESS = "invalid_broadcast_address"
    INVALID_MAC_ADDRESS = "invalid_mac_address"
