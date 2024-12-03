"""Config flow for tesy integration."""
import logging

import voluptuous as vol
import asyncio

from homeassistant import config_entries, core, exceptions
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.const import (
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    CONF_RESOURCES,
)

from .const import *  # pylint:disable=unused-import
from .tesy_water_heater import WaterHeater

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
DATA_SCHEMA = vol.Schema({"host": str})


class PlaceholderHub:
    """Placeholder class to make tests pass.

    TODO Remove this placeholder class and replace with things from your PyPI package.
    """

    def __init__(self, host):
        """Initialize."""
        self.host = host

#    async def authenticate(self, username, password) -> bool:
#        """Test if we can authenticate with the host."""
#        return True


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )

    hub = PlaceholderHub(data["host"])

#    if not await hub.authenticate(data["username"], data["password"]):
#        raise InvalidAuth

    tesyWH = WaterHeater(hub.host)
    try:
        await hass.async_add_executor_job(tesyWH.getDeviceInfo)
    except ConnectionError:
        raise CannotConnect
    except TimeoutError:
        raise CannotConnect

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    device = tesyWH.device
    return {"title": device['devid'] }

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for tesy."""

    VERSION = 1
    # TODO pick one of the available connection classes in homeassistant/config_entries.py
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
#                info = await validate_input(self.hass, user_input)
                tesyWH = WaterHeater(user_input["host"])
                await self.hass.async_add_executor_job(tesyWH.getDeviceInfo)
                await self.async_set_unique_id(tesyWH.device['devid'])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=tesyWH.device['devid'], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for tesy."""
        
    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        
#        resources = find_resources_in_config_entry(self.config_entry)
        scan_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
    
        return self.async_show_form(
            step_id="init", 
            data_schema=vol.Schema(
              {
                vol.Optional(CONF_SCAN_INTERVAL, default=scan_interval): cv.positive_int
              }),
        )

class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
