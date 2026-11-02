"""Elektrobock PT32 WiFi – termostat přes cloud Elektrobock."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers.event import async_track_time_interval

from .const import POLL_SECONDS
from .hub import AuthError, PT32Hub, async_fetch_devices

PLATFORMS = [Platform.CLIMATE, Platform.BINARY_SENSOR]


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

    entry.async_on_unload(async_track_time_interval(hass, _poll, timedelta(seconds=POLL_SECONDS)))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        for hub in entry.runtime_data:
            await hub.async_stop()
    return unloaded
