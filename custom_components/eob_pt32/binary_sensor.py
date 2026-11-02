"""Indikátor sepnutí kotle."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ST_STATE, STATE_HEATING
from .entity import PT32Entity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(PT32Boiler(hub) for hub in entry.runtime_data)


class PT32Boiler(PT32Entity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.HEAT
    _attr_translation_key = "boiler"
    _attr_icon = "mdi:fire"

    def __init__(self, hub) -> None:
        super().__init__(hub, "boiler")

    @property
    def is_on(self) -> bool | None:
        st = self._hub.status
        return bool(st[ST_STATE] & STATE_HEATING) if st else None
