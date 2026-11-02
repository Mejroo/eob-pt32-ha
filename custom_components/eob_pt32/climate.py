"""Termostat PT32 WiFi jako entita climate."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    ITEM_CLOCK,
    MODE_AUTO,
    MODE_KEEP_MASK,
    RELAY_HEATING,
    ST_ACTUAL,
    ST_AUTO,
    ST_DESIRED,
    ST_FLAGS,
    ST_RELAY,
    TEMP_MAX,
    TEMP_MIN,
)
from .hub import PT32Hub


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(PT32Climate(hub) for hub in entry.runtime_data)


class PT32Climate(ClimateEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5
    _attr_min_temp = TEMP_MIN
    _attr_max_temp = TEMP_MAX
    # HEAT = ruční teplota, AUTO = týdenní program termostatu.
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.AUTO]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

    def __init__(self, hub: PT32Hub) -> None:
        self._hub = hub
        self._attr_unique_id = f"pt32_{hub.device_id}"
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
        return self._hub.connected and self._hub.status is not None

    @property
    def current_temperature(self) -> float | None:
        st = self._hub.status
        return float(st[ST_ACTUAL]) if st else None

    @property
    def target_temperature(self) -> float | None:
        st = self._hub.status
        return st[ST_DESIRED] / 2 if st else None

    @property
    def hvac_mode(self) -> HVACMode | None:
        st = self._hub.status
        if not st:
            return None
        return HVACMode.AUTO if st[ST_AUTO] & 0x01 else HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction | None:
        st = self._hub.status
        if not st:
            return None
        return HVACAction.HEATING if st[ST_RELAY] & RELAY_HEATING else HVACAction.IDLE

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

    def _mode_byte(self, auto: bool) -> int:
        st = self._hub.status
        keep = (st[ST_FLAGS] & MODE_KEEP_MASK) if st else 0x20
        return keep | (MODE_AUTO if auto else 0)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        mode = kwargs.get("hvac_mode") or self.hvac_mode
        self._hub.write_status(self._mode_byte(mode == HVACMode.AUTO), float(temperature))

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        target = self.target_temperature or 20.0
        self._hub.write_status(self._mode_byte(hvac_mode == HVACMode.AUTO), target)
