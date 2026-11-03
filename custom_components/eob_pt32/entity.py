"""Společný základ entit termostatu PT32 WiFi."""

from __future__ import annotations

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .hub import PT32Hub, WriteError


class PT32Entity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hub: PT32Hub, key: str) -> None:
        self._hub = hub
        # Climate si ponechá původní unique_id, aby se po aktualizaci nezměnilo entity_id.
        self._attr_unique_id = f"pt32_{hub.device_id}" if key == "climate" else f"pt32_{hub.device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(hub.device_id))},
            name=hub.name,
            manufacturer="Elektrobock",
            model="PT32 WiFi",
            sw_version=hub.firmware,
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._hub.add_listener(self.async_write_ha_state))

    @property
    def available(self) -> bool:
        return self._hub.online and self._hub.status is not None

    async def _async_guard(self, write) -> None:
        """Provede zápis; nepotvrzený zápis ohlásí v HA jako chybu."""
        try:
            await write
        except WriteError as err:
            raise HomeAssistantError(f"{self._hub.name}: {err}") from err
