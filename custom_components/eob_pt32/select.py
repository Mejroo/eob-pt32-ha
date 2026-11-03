"""Výběr programu termostatu (Hlavni program, Program 002 …) s týdenním rozvrhem."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import MODE_AUTO, MODE_KEEP_MASK, PROGRAM_COUNT, ST_DESIRED, ST_FLAGS, ST_PROGRAM
from .entity import PT32Entity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(PT32ProgramSelect(hub) for hub in entry.runtime_data)


class PT32ProgramSelect(PT32Entity, SelectEntity):
    _attr_translation_key = "program"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, hub) -> None:
        super().__init__(hub, "program")

    def _name(self, number: int) -> str:
        return self._hub.programs.get(number) or f"Program {number:03d}"

    @property
    def options(self) -> list[str]:
        return [self._name(n) for n in range(1, PROGRAM_COUNT + 1)]

    @property
    def current_option(self) -> str | None:
        st = self._hub.status
        return self._name(st[ST_PROGRAM]) if st and st[ST_PROGRAM] else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        # Rozvrh aktivního programu po dnech, např. Po: "00:00 20 °C, 05:00 21 °C, 19:00 20 °C".
        st = self._hub.status
        schedule = self._hub.schedules.get(st[ST_PROGRAM]) if st else None
        if not schedule:
            return {}
        return {
            day: ", ".join(f"{time} {temp:g} °C" for time, temp in slots) for day, slots in schedule.items()
        }

    async def async_select_option(self, option: str) -> None:
        number = self.options.index(option) + 1
        st = self._hub.status
        # Program platí v režimu auto – stejně jako v aplikaci se zároveň přepne do auto.
        mode_byte = ((st[ST_FLAGS] & MODE_KEEP_MASK) if st else 0x20) | MODE_AUTO
        desired = st[ST_DESIRED] / 2 if st and st[ST_DESIRED] else 20.0
        await self._async_guard(self._hub.async_write_status(number, mode_byte, desired))
