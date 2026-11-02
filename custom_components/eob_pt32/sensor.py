"""Doba provozu kotle počítaná termostatem."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import PT32Entity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(PT32BoilerHours(hub) for hub in entry.runtime_data)


class PT32BoilerHours(PT32Entity, SensorEntity):
    _attr_translation_key = "boiler_hours"
    _attr_icon = "mdi:timer-outline"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_suggested_display_precision = 1

    def __init__(self, hub) -> None:
        super().__init__(hub, "boiler_hours")

    @property
    def available(self) -> bool:
        return self._hub.connected and self._hub.boiler_minutes is not None

    @property
    def native_value(self) -> float | None:
        minutes = self._hub.boiler_minutes
        return round(minutes / 60, 2) if minutes is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        minutes = self._hub.boiler_minutes
        return {"hh_mm": f"{minutes // 60}:{minutes % 60:02d}"} if minutes is not None else {}
