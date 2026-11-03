"""Senzory termostatu: doba provozu kotle, údržba kotle, firmware a poslední odpověď."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import SET_SERVICE_DAY, SET_SERVICE_MONTH, SET_SERVICE_YEAR
from .entity import PT32Entity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(
        entity
        for hub in entry.runtime_data
        for entity in (PT32BoilerHours(hub), PT32ServiceDate(hub), PT32Firmware(hub), PT32LastSeen(hub))
    )


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
        return self._hub.online and self._hub.boiler_minutes is not None

    @property
    def native_value(self) -> float | None:
        minutes = self._hub.boiler_minutes
        return round(minutes / 60, 2) if minutes is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        minutes = self._hub.boiler_minutes
        return {"hh_mm": f"{minutes // 60}:{minutes % 60:02d}"} if minutes is not None else {}


class PT32ServiceDate(PT32Entity, SensorEntity):
    """Datum údržby kotle z nastavení termostatu (RR, RM, RD; 26, 02, 08 = 8. 3. 2026)."""

    _attr_translation_key = "service_date"
    _attr_icon = "mdi:wrench-clock"
    _attr_device_class = SensorDeviceClass.DATE
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hub) -> None:
        super().__init__(hub, "service_date")

    @property
    def native_value(self) -> date | None:
        year, month, day = (self._hub.setting(c) for c in (SET_SERVICE_YEAR, SET_SERVICE_MONTH, SET_SERVICE_DAY))
        if year is None or month is None or day is None:
            return None
        try:
            # Měsíc termostat počítá od nuly (aplikace ukazuje 8. 3. 26 pro 02).
            return date(2000 + year, month + 1, day)
        except ValueError:
            return None

    @property
    def available(self) -> bool:
        return self._hub.online and self.native_value is not None


class PT32Firmware(PT32Entity, SensorEntity):
    _attr_translation_key = "firmware"
    _attr_icon = "mdi:chip"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hub) -> None:
        super().__init__(hub, "firmware")

    @property
    def available(self) -> bool:
        return self._hub.firmware_version is not None

    @property
    def native_value(self) -> str | None:
        return self._hub.firmware_version


class PT32LastSeen(PT32Entity, SensorEntity):
    """Čas poslední odpovědi termostatu; dostupný i ve chvíli, kdy termostat neodpovídá."""

    _attr_translation_key = "last_seen"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hub) -> None:
        super().__init__(hub, "last_seen")

    @property
    def available(self) -> bool:
        return self._hub.last_seen is not None

    @property
    def native_value(self) -> datetime | None:
        return self._hub.last_seen
