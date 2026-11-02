"""Termostat PT32 WiFi jako entita climate."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ITEM_CLOCK,
    MODE_AUTO,
    MODE_KEEP_MASK,
    MODE_OFF,
    ST_ACTUAL,
    ST_ACTUAL_TENTHS,
    ST_AUTO,
    ST_DESIRED,
    ST_FLAGS,
    ST_STATE,
    STATE_HEATING,
    STATE_OFF,
    TEMP_MAX,
    TEMP_MIN,
)
from .entity import PT32Entity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(PT32Climate(hub) for hub in entry.runtime_data)


class PT32Climate(PT32Entity, ClimateEntity):
    _attr_name = None
    _attr_translation_key = "pt32"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5
    _attr_min_temp = TEMP_MIN
    _attr_max_temp = TEMP_MAX
    # AUTO = program termostatu, HEAT = manual (nastavitelná teplota), OFF = vypnuto.
    _attr_hvac_modes = [HVACMode.AUTO, HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, hub) -> None:
        super().__init__(hub, "climate")

    @property
    def current_temperature(self) -> float | None:
        st = self._hub.status
        return st[ST_ACTUAL] + st[ST_ACTUAL_TENTHS] / 10 if st else None

    @property
    def target_temperature(self) -> float | None:
        st = self._hub.status
        if not st or self.hvac_mode == HVACMode.OFF:
            return None
        return st[ST_DESIRED] / 2

    @property
    def hvac_mode(self) -> HVACMode | None:
        st = self._hub.status
        if not st:
            return None
        if st[ST_STATE] & STATE_OFF:
            return HVACMode.OFF
        return HVACMode.AUTO if st[ST_AUTO] & 0x01 else HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction | None:
        st = self._hub.status
        if not st:
            return None
        if st[ST_STATE] & STATE_OFF:
            return HVACAction.OFF
        return HVACAction.HEATING if st[ST_STATE] & STATE_HEATING else HVACAction.IDLE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        st = self._hub.status
        clock = self._hub.items.get(ITEM_CLOCK)
        attrs: dict[str, Any] = {}
        if st:
            attrs["keyboard_locked"] = bool(st[ST_FLAGS] & 0x40)
            attrs["raw_status"] = st.hex()
        if clock and len(clock) >= 6:
            attrs["thermostat_clock"] = f"20{clock[0]:02d}-{clock[1]:02d}-{clock[2]:02d} {clock[3]:02d}:{clock[4]:02d}:{clock[5]:02d}"
        return attrs

    def _write(self, hvac_mode: HVACMode, temperature: float | None = None) -> None:
        st = self._hub.status
        mode_byte = (st[ST_FLAGS] & MODE_KEEP_MASK) if st else 0x20
        if hvac_mode == HVACMode.AUTO:
            mode_byte |= MODE_AUTO
        elif hvac_mode == HVACMode.OFF:
            mode_byte |= MODE_OFF
        if temperature is None:
            temperature = (st[ST_DESIRED] / 2 if st and st[ST_DESIRED] else None) or 20.0
        self._hub.write_status(mode_byte, temperature)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        # V auto se teplota řídí programem; ruční změna přepne na manual, stejně jako na termostatu.
        self._write(HVACMode.HEAT, float(temperature))

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        self._write(hvac_mode)

    async def async_turn_on(self) -> None:
        self._write(HVACMode.AUTO)

    async def async_turn_off(self) -> None:
        self._write(HVACMode.OFF)
