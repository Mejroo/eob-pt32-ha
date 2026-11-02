"""Elektrobock PT32 WiFi – termostat přes cloud Elektrobock."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import async_track_time_interval

from .const import BOILER_POLL_SECONDS, DOMAIN, POLL_SECONDS, SLOW_POLL_SECONDS
from .hub import AuthError, PT32Hub, async_fetch_devices

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CLIMATE, Platform.BINARY_SENSOR, Platform.SELECT, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    try:
        devices = await async_fetch_devices(hass, entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
    except AuthError as err:
        raise ConfigEntryError("Špatné přihlašovací údaje k účtu Elektrobock") from err
    except Exception as err:  # noqa: BLE001 – server nedostupný, HA zkusí znovu
        raise ConfigEntryNotReady(str(err)) from err

    hubs = [PT32Hub(hass, d) for d in devices]
    for hub in hubs:
        await hub.async_start()
    entry.runtime_data = hubs

    def _poll(_now) -> None:
        for hub in hubs:
            hub.request_state()

    def _poll_boiler(_now) -> None:
        for hub in hubs:
            hub.request_boiler_hours()

    async def _poll_slow(_now) -> None:
        # Názvy programů z termostatu a název termostatu z účtu (přejmenování v aplikaci).
        for hub in hubs:
            await hub.async_request_programs()
        try:
            fresh = await async_fetch_devices(hass, entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("PT32: název z účtu se nepodařilo načíst: %s", err)
            return
        registry = dr.async_get(hass)
        for device in fresh:
            hub = next((h for h in hubs if h.device_id == device["deviceId"]), None)
            name = device.get("name")
            if hub is None or not name or name == hub.name:
                continue
            hub.name = name
            if entry_device := registry.async_get_device(identifiers={(DOMAIN, str(hub.device_id))}):
                registry.async_update_device(entry_device.id, name=name)

    entry.async_on_unload(async_track_time_interval(hass, _poll, timedelta(seconds=POLL_SECONDS)))
    entry.async_on_unload(async_track_time_interval(hass, _poll_boiler, timedelta(seconds=BOILER_POLL_SECONDS)))
    entry.async_on_unload(async_track_time_interval(hass, _poll_slow, timedelta(seconds=SLOW_POLL_SECONDS)))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        for hub in entry.runtime_data:
            await hub.async_stop()
    return unloaded
