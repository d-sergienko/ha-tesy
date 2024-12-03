"""The tesy integration."""
import asyncio
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    CONF_HOST,
    CONF_RESOURCES,
    CONF_SCAN_INTERVAL,
)


from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS = ["water_heater"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the tesy component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up tesy from a config entry."""
    # TODO Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
#    if unload_ok:
#        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

async def update_listener(hass, config_entry):
    """Update when config_entry options update."""
    if not config_entry.options:
        return

    _LOGGER.warning(
        "Changing scan_interval to %s",
        config_entry.options[CONF_SCAN_INTERVAL],
    )

    if config_entry.options[CONF_SCAN_INTERVAL] is None:
        return

    await hass.config_entries.async_reload(config_entry.entry_id)
