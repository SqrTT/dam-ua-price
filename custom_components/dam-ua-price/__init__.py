
from __future__ import annotations
from typing import Any
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

from .const import DOMAIN, LOGGER, PLATFORMS
from .coordinator import DAMDataUpdateCoordinator
# from .services import async_setup_services

type DAMConfigEntry = ConfigEntry[DAMDataUpdateCoordinator]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the service."""

    #async_setup_services(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant, config_entry: DAMConfigEntry
) -> bool:
    """Set up from a config entry."""

    await cleanup_device(hass, config_entry)

    coordinator = DAMDataUpdateCoordinator(hass, config_entry)
    await coordinator.init()
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="initial_update_failed",
            translation_placeholders={"error": str(coordinator.last_exception)},
        )
    config_entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, config_entry: DAMConfigEntry
) -> bool:
    """Unload config entry."""
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


async def cleanup_device(
    hass: HomeAssistant, config_entry: DAMConfigEntry
) -> None:
    """Cleanup device and entities."""
    device_reg = dr.async_get(hass)

    entries = dr.async_entries_for_config_entry(device_reg, config_entry.entry_id)
    for entry in entries:
        if entry.identifiers == {(DOMAIN)}:
            continue

        LOGGER.debug("Removing device %s", entry.name)
        device_reg.async_update_device(
            entry.id, remove_config_entry_id=config_entry.entry_id
        )
