"""Config flow for Unfolded Circle Remote integration."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_NAME, CONF_HOST
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from sonyapilib.device import SonyDevice, AuthenticationResult

from .const import (DOMAIN, DEFAULT_DEVICE_NAME,
                    CONF_PIN,
                    CONF_MAC_ADDRESS, CONF_BROADCAST_ADDRESS,
                    CONF_APP_PORT, DEFAULT_APP_PORT, CONF_DMR_PORT,
                    CONF_UPDATE_INTERVAL,
                    CONF_AUTHENTICATED,
                    DEFAULT_PIN,
                    DEFAULT_BROADCAST_ADDRESS,
                    DEFAULT_DMR_PORT, CONF_IRCC_PORT, DEFAULT_IRCC_PORT,
                    DEFAULT_UPDATE_INTERVAL)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Optional(CONF_NAME): str,  # TODO: Use for device and remote name
    vol.Required(CONF_HOST): str,
    vol.Optional(CONF_MAC_ADDRESS): str,
    vol.Optional(CONF_BROADCAST_ADDRESS,
                 default=DEFAULT_BROADCAST_ADDRESS): str,
    vol.Optional(CONF_APP_PORT, default=DEFAULT_APP_PORT): int,
    vol.Optional(CONF_DMR_PORT, default=DEFAULT_DMR_PORT): int,
    vol.Optional(CONF_IRCC_PORT, default=DEFAULT_IRCC_PORT): int,
    vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): int
})

# TODO: Move advanced stuff to this section
# STEP_ADVANCED_DATA_SCHEMA = vol.Schema({
#    vol.Optional(CONF_MAC_ADDRESS): str,
#    vol.Optional(CONF_BROADCAST_ADDRESS,
#                 default=DEFAULT_BROADCAST_ADDRESS): str,
#    vol.Optional(CONF_APP_PORT, default=DEFAULT_APP_PORT): int,
#    vol.Optional(CONF_DMR_PORT, default=DEFAULT_DMR_PORT): int,
#    vol.Optional(CONF_IRCC_PORT, default=DEFAULT_IRCC_PORT): int,
# })

STEP_PIN_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_PIN, default=DEFAULT_PIN): str
})


# TODO: Sony device supports SSDP discovery
def validate_input(user_input: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA
    with values provided by the user.
    """
    _LOGGER.debug("Sony device user input %s", user_input)
    # errors = {}

    pin = user_input.get(CONF_PIN)
    broadcast_address = user_input.get(CONF_BROADCAST_ADDRESS)
    # TODO: Validate mac address, broadcast address, and other inputs

    sony_device = SonyDevice(user_input[CONF_HOST], DEFAULT_DEVICE_NAME,
                             broadcast_address=broadcast_address,
                             app_port=user_input[CONF_APP_PORT],
                             dmr_port=user_input[CONF_DMR_PORT],
                             ircc_port=user_input[CONF_IRCC_PORT])
    authenticated = False

    if not pin or pin == DEFAULT_PIN:
        register_result = sony_device.register()

        if register_result == AuthenticationResult.SUCCESS:
            authenticated = True
        elif register_result == AuthenticationResult.PIN_NEEDED:
            # return so next call has the correct pin
            config = {"error": AuthenticationResult.PIN_NEEDED}
            config.update(user_input)

            return config
        else:
            _LOGGER.error("An unknown error occurred during registration")

            config = {"error": register_result}
            config.update(user_input)

            return config

    if not authenticated:
        authenticated = sony_device.send_authentication(pin)

    # Return info that you want to store in the config entry.
    config = {
        CONF_AUTHENTICATED: authenticated,
        CONF_MAC_ADDRESS: sony_device.mac
        # "device_info": sony_device.save_to_json()
    }
    config.update(user_input)

    return config


class SonyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Unfolded Circle Remote."""

    VERSION = 1
    MINOR_VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    reauth_entry: ConfigEntry | None = None
    user_input: dict[str, Any] | None = None

    def __init__(self) -> None:
        """Sony Config Flow."""
        self.api: SonyDevice | None = None

        self.discovery_info: dict[str, Any] = {}

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if not user_input or user_input == {}:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors
            )

        if not self.user_input:
            self.user_input = user_input
        else:
            self.user_input.update(user_input)

        try:
            info = await self.hass.async_add_executor_job(validate_input,
                                                          self.user_input)

            if info.get("error") == AuthenticationResult.PIN_NEEDED:
                errors["base"] = "invalid_auth"

                return self.async_show_form(
                    step_id="user",
                    data_schema=STEP_PIN_DATA_SCHEMA,
                    errors=errors,
                )
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except ValueError as ex:
            _LOGGER.exception("Unexpected exception", ex)

            errors["base"] = "cannot_connect"
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception", ex)

            errors["base"] = "unknown"
        else:
            host = self.user_input[CONF_HOST]

            if len(errors.keys()) == 0:
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=f"Sony Device ({host})",
                                               data=info)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors
        )

    # TODO:
    # async def async_step_reauth(
    #         self, user_input: dict[str, Any] | None = None
    # ) -> FlowResult:
    #     """Perform reauth upon an API authentication error."""
    #     user_input["pin"] = None
    #     user_input["apiKey"] = None
    #     return await self.async_step_reauth_confirm(user_input)
    #
    # async def async_step_reauth_confirm(
    #         self, user_input: dict[str, Any] | None = None
    # ) -> FlowResult:
    #     """Dialog that informs the user that reauth is required."""
    #     errors = {}
    #     if user_input is None:
    #         user_input = {}
    #
    #     self.reauth_entry = self.hass.config_entries.async_get_entry(
    #         self.context["entry_id"]
    #     )
    #
    #     _LOGGER.debug("RC2 async_step_reauth_confirm %s", self.reauth_entry)
    #
    #     if user_input.get("pin") is None:
    #         return self.async_show_form(
    #             step_id="reauth_confirm",
    #             data_schema=STEP_ZEROCONF_DATA_SCHEMA
    #         )
    #
    #     try:
    #         existing_entry = await self.async_set_unique_id(
    #             self.reauth_entry.unique_id
    #         )
    #         _LOGGER.debug("RC2 existing_entry %s", existing_entry)
    #         info = await validate_input(user_input,
    #                                     self.reauth_entry.data[CONF_HOST])
    #     except CannotConnect:
    #         _LOGGER.exception("Cannot Connect")
    #         errors["base"] = "Cannot Connect"
    #     except InvalidAuth:
    #         _LOGGER.exception("Invalid PIN")
    #         errors["base"] = "Invalid PIN"
    #     except Exception as ex:  # pylint: disable=broad-except
    #         _LOGGER.exception(ex)
    #         errors["base"] = "unknown"
    #     else:
    #         existing_entry = await self.async_set_unique_id(
    #             self.reauth_entry.unique_id
    #         )
    #         if existing_entry:
    #             self.hass.config_entries.async_update_entry(existing_entry,
    #                                                         data=info)
    #             await self.hass.config_entries.async_reload(
    #                 existing_entry.entry_id
    #             )
    #             return self.async_abort(reason="reauth_successful")
    #
    #         return self.async_create_entry(
    #             title=info["title"],
    #             data=info,
    #         )
    #     return self.async_show_form(
    #         step_id="reauth_confirm",
    #         data_schema=STEP_ZEROCONF_DATA_SCHEMA,
    #         errors=errors,
    #     )


class SonyDeviceOptionsFlowHandler(OptionsFlow):
    """Handle Unfolded Circle Remote options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
            self, user_input: dict[str, int] | None = None
    ) -> FlowResult:
        """Manage Unfolded Circle options."""
        if user_input:
            return self.async_create_entry(title="",
                                           data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=STEP_USER_DATA_SCHEMA,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
