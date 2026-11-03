"""Nastavení termostatu s číselnou hodnotou (korekce teploty, hystereze, min. doba zapnutí).

Zapisují se jen položky, jejichž zápis byl ověřen odposlechem aplikace EOB PT-WIFI.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import SET_HYSTERESIS, SET_MIN_ON, SET_OFFSET
from .entity import PT32Entity


@dataclass(frozen=True, kw_only=True)
class PT32NumberDescription(NumberEntityDescription):
    code: int
    to_value: Callable[[int], float]
    to_raw: Callable[[float], int]


NUMBERS = (
    # 0x57 = −1,3 °C, 0x58 = −1,2 °C (ověřeno v aplikaci).
    PT32NumberDescription(
        key="offset",
        translation_key="offset",
        icon="mdi:thermometer-plus",
        code=SET_OFFSET,
        native_min_value=-5.0,
        native_max_value=5.0,
        native_step=0.1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        to_value=lambda raw: (raw - 100) / 10,
        to_raw=lambda value: int(round(value * 10)) + 100,
    ),
    # 0x03 = 0,3 °C, 0x04 = 0,4 °C.
    PT32NumberDescription(
        key="hysteresis",
        translation_key="hysteresis",
        icon="mdi:arrow-expand-vertical",
        code=SET_HYSTERESIS,
        native_min_value=0.1,
        native_max_value=1.0,
        native_step=0.1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        to_value=lambda raw: raw / 10,
        to_raw=lambda value: int(round(value * 10)),
    ),
    # Minuty, 5 ↔ 4 ověřeno.
    PT32NumberDescription(
        key="min_on_time",
        translation_key="min_on_time",
        icon="mdi:timer-cog-outline",
        code=SET_MIN_ON,
        native_min_value=1,
        native_max_value=10,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        to_value=lambda raw: raw,
        to_raw=lambda value: int(value),
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(PT32Number(hub, desc) for hub in entry.runtime_data for desc in NUMBERS)


class PT32Number(PT32Entity, NumberEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX
    entity_description: PT32NumberDescription

    def __init__(self, hub, description: PT32NumberDescription) -> None:
        super().__init__(hub, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        return self._hub.online and self._hub.setting(self.entity_description.code) is not None

    @property
    def native_value(self) -> float | None:
        raw = self._hub.setting(self.entity_description.code)
        return self.entity_description.to_value(raw) if raw is not None else None

    async def async_set_native_value(self, value: float) -> None:
        desc = self.entity_description
        await self._async_guard(self._hub.async_write_setting(desc.code, desc.to_raw(value)))
