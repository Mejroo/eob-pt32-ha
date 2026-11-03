"""Indikátor sepnutí kotle a spojení s termostatem."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ST_STATE, STATE_HEATING
from .entity import PT32Entity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(entity for hub in entry.runtime_data for entity in (PT32Boiler(hub), PT32Online(hub)))


class PT32Boiler(PT32Entity, BinarySensorEntity):
    _attr_translation_key = "boiler"
    _attr_icon = "mdi:fire"

    def __init__(self, hub) -> None:
        super().__init__(hub, "boiler")

    @property
    def is_on(self) -> bool | None:
        st = self._hub.status
        return bool(st[ST_STATE] & STATE_HEATING) if st else None


class PT32Online(PT32Entity, BinarySensorEntity):
    """Termostat odpovídá přes cloud (spojení s brokerem a odpověď za poslední 3 minuty)."""

    _attr_translation_key = "online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hub) -> None:
        super().__init__(hub, "online")

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        return self._hub.online
