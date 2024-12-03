"""Support for Rheem EcoNet water heaters."""
import datetime
import logging

import voluptuous as vol
from .tesy_water_heater import WaterHeater
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv, entity_platform, service
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.entity_component import EntityComponent
from datetime import timedelta


from homeassistant.components.water_heater import (
    PLATFORM_SCHEMA,
    STATE_ECO,
    STATE_OFF,
    STATE_ON,
    STATE_PERFORMANCE,
    SUPPORT_OPERATION_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_AWAY_MODE,
    WaterHeaterEntity,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    TEMP_CELSIUS,
    PRECISION_WHOLE,
    CONF_HOST,
    CONF_SCAN_INTERVAL,
)

from .const import *

_LOGGER = logging.getLogger(__name__)

SERVICE_BOOST_ON = "boost_on"
SERVICE_BOOST_OFF = "boost_off"
ATTR_BOOST = "boost"

SET_BOOST_MODE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.comp_entity_ids,
    }
)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,

})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Tesy water heaters."""
    _LOGGER.debug("inside setup_platform")
    wh = WaterHeater(config[CONF_HOST])
    add_entities(TesyWaterHeater(wh))

async def async_setup(hass, config):
     """Set up water_heater devices."""
     _LOGGER.debug("inside async_setup")
     component = hass.data[DOMAIN] = EntityComponent(
         _LOGGER, DOMAIN, hass, config.options.get(CONF_SCAN_INTERVAL)
     )
     await component.async_setup(config)

     component.async_register_entity_service(
         SERVICE_BOOST_OFF, SET_BOOST_MODE_SCHEMA, "turn_boost_off"
     )
     component.async_register_entity_service(
         SERVICE_BOOST_ON, SET_BOOST_MODE_SCHEMA, "turn_boost_on"
     )
    
     return True



async def async_setup_entry(hass, config_entry, async_add_entities):
    _LOGGER.debug("inside async_setup_entry")
    wh = WaterHeater(config_entry.data[CONF_HOST])
    await hass.async_add_executor_job(wh.getDeviceInfo)
    await hass.async_add_executor_job(wh.getStatus)
    twh = TesyWaterHeater(wh)
    async_add_entities([twh], True)

    platform = entity_platform.current_platform.get()
    platform.async_register_entity_service(
        SERVICE_BOOST_OFF, SET_BOOST_MODE_SCHEMA, "turn_boost_off"
    )
    platform.async_register_entity_service(
        SERVICE_BOOST_ON, SET_BOOST_MODE_SCHEMA, "turn_boost_on"
    )

    return True


class TesyWaterHeater(WaterHeaterEntity):
    """Representation of an EcoNet water heater."""

    def __init__(self, tesy_water_heater):
        """Initialize the water heater."""
        self.water_heater = tesy_water_heater

    @property
    def name(self):
        """Return the device name."""
        return "Tesy " + self.water_heater.getDeviceID()

    @property
    def unique_id(self):
        """Return the device ID."""
        return self.water_heater.getDeviceID()

    @property
    def current_operation(self):
        """
        Return current operation as one of the following.

        ["eco", "heat_pump", "high_demand", "electric_only"]
        """
        return self.water_heater.getMode()
    
    @property
    def operation_list(self):
        """List of available operation modes."""
        return self.water_heater.modes[1:]
    
    def set_operation_mode(self, operation_mode):                                                          
        """Set operation mode."""
        if operation_mode is not None:                                                                     
            self.water_heater.setMode(self.water_heater.modes.index(operation_mode))
        else:
            _LOGGER.error("An operation mode must be provided")

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def precision(self):
        """Return the precision of the system."""
        return PRECISION_WHOLE

    @property
    def extra_state_attributes(self):
        """Return the optional device state attributes."""
        data = {
            ATTR_BOOST: bool(int(self.water_heater.status['boost']))
        }

        return data

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE | SUPPORT_AWAY_MODE

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        if target_temp is not None:
            self.water_heater.setTemp(target_temp)
        else:
            _LOGGER.error("A target temperature must be provided")

    def update(self):
        """Get the latest date."""
        _LOGGER.debug("inside update")
        self.water_heater.getStatus()

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return round(float(self.water_heater.status['ref_gradus']))

    @property
    def current_temperature(self):
        """Return the temperature we try to reach."""
        return round(float(self.water_heater.status['gradus']))

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return 8
    
    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return 75

    @property
    def is_away_mode_on(self):
        return (self.water_heater.status['power_sw'] != 'on')
    
    def turn_away_mode_on(self):
        _LOGGER.debug("inside turn_away_mode_off")
        self.water_heater.powerOff()

    def turn_away_mode_off(self):
        _LOGGER.debug("inside turn_away_mode_on")
        self.water_heater.powerOn()

    def turn_boost_on(self):
        _LOGGER.debug("inside turn_boost_on")
        self.water_heater.boostOn()

    def turn_boost_off(self):
        _LOGGER.debug("inside turn_boost_off")
        self.water_heater.boostOff()

    async def async_update(self):
      try:
        await self.hass.async_add_executor_job(self.update)
      except:
        _LOGGER.exception(
              f"Error updating tesy: "
            )
