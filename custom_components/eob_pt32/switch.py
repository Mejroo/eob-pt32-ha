"""Zámek klávesnice termostatu (položka LK, hodnoty „A“ / „N“ jako v aplikaci)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import NO, SET_LOCK, YES
from .entity import PT32Entity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(PT32KeyLock(hub) for hub in entry.runtime_data)


class PT32KeyLock(PT32Entity, SwitchEntity):
    _attr_translation_key = "key_lock"
    _attr_icon = "mdi:lock"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hub) -> None:
        super().__init__(hub, "key_lock")

    @property
    def available(self) -> bool:
        return self._hub.online and self._hub.setting(SET_LOCK) is not None

    @property
    def is_on(self) -> bool | None:
        raw = self._hub.setting(SET_LOCK)
        return raw == YES if raw is not None else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_guard(self._hub.async_write_setting(SET_LOCK, YES))

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_guard(self._hub.async_write_setting(SET_LOCK, NO))
