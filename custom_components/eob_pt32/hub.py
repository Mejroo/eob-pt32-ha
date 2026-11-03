"""Spojení s termostatem PT32 WiFi přes cloud Elektrobock (REST + MQTT přes WebSocket)."""

from __future__ import annotations

import asyncio
import base64
import logging
import random
import ssl
import string
from collections.abc import Callable
from datetime import datetime

import paho.mqtt.client as mqtt

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import (
    API_BASE,
    API_DEVICES,
    API_LOGIN,
    DAY_NAMES,
    DEVICE_TYPE_PT32_WIFI,
    FRAME_REQUEST,
    FRAME_RESPONSE,
    ITEM_BOILER_HOURS,
    ITEM_CLOCK,
    ITEM_FIRMWARE,
    ITEM_PROGRAM,
    ITEM_STATUS,
    LEN_MASK,
    MQTT_HOST,
    MQTT_PORT,
    MQTT_WS_PATH,
    OFFLINE_SECONDS,
    PROGRAM_COUNT,
    PROGRAM_DAY_SLOTS,
    PROGRAM_NAME_LEN,
    READ_FLAG,
    SETTINGS_READ,
    TOPIC_BASE,
    WRITE_ATTEMPTS,
    WRITE_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class AuthError(Exception):
    """Špatné přihlašovací údaje."""


class WriteError(Exception):
    """Termostat zápis nepotvrdil."""


async def async_fetch_devices(hass: HomeAssistant, username: str, password: str) -> list[dict]:
    """Přihlásí se a vrátí termostaty PT32 WiFi v účtu."""
    session = async_get_clientsession(hass)
    async with session.post(API_BASE + API_LOGIN, json={"userName": username, "password": password}) as resp:
        if resp.status in (400, 401, 403):
            raise AuthError
        resp.raise_for_status()
        account = await resp.json()
    token = account["authToken"]
    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(API_BASE + API_DEVICES, headers=headers, params={"userId": str(account["id"])}) as resp:
        resp.raise_for_status()
        devices = await resp.json()
    return [d for d in devices or [] if d.get("deviceType") == DEVICE_TYPE_PT32_WIFI]


def build_frame(items: list[tuple[int, bytes]]) -> bytes:
    body = b"".join(t.to_bytes(2, "big") + len(d).to_bytes(2, "big") + d for t, d in items)
    return FRAME_REQUEST.to_bytes(2, "big") + len(body).to_bytes(2, "big") + body


def parse_frame(frame: bytes) -> dict[int, bytes]:
    """Vrátí {typ položky: data} z odpovědi termostatu; chybové odpovědi ignoruje."""
    if len(frame) < 4 or int.from_bytes(frame[0:2], "big") != FRAME_RESPONSE:
        return {}
    end = min(len(frame), 4 + (int.from_bytes(frame[2:4], "big") & LEN_MASK))
    items: dict[int, bytes] = {}
    pos = 4
    while pos + 4 <= end:
        item_type = int.from_bytes(frame[pos : pos + 2], "big") & ~READ_FLAG
        length = int.from_bytes(frame[pos + 2 : pos + 4], "big") & LEN_MASK
        items[item_type] = frame[pos + 4 : pos + 4 + length]
        pos += 4 + length
    return items


def decode_schedule(data: bytes) -> dict[str, list[tuple[str, float]]]:
    """Týdenní rozvrh z dat programu: {den: [(čas, teplota)]}, opakované úseky vynechá.

    Den má 6 párů [čas][teplota × 2]; čas je v osminách hodiny (0x28 = 5:00, 0x98 = 19:00).
    Nepoužité úseky termostat vyplní kopií předchozího.
    """
    size = PROGRAM_DAY_SLOTS * 2
    schedule: dict[str, list[tuple[str, float]]] = {}
    for day, name in enumerate(DAY_NAMES):
        chunk = data[day * size : (day + 1) * size]
        if len(chunk) < size:
            break
        slots: list[tuple[str, float]] = []
        for i in range(0, size, 2):
            minutes = chunk[i] * 60 // 8
            slot = (f"{minutes // 60:02d}:{minutes % 60:02d}", chunk[i + 1] / 2)
            if not slots or slots[-1] != slot:
                slots.append(slot)
        schedule[name] = slots
    return schedule


class PT32Hub:
    """Jeden termostat: drží MQTT spojení a poslední známý stav."""

    def __init__(self, hass: HomeAssistant, device: dict) -> None:
        self.hass = hass
        self.device_id = device["deviceId"]
        self.name = device.get("name") or "PT32 WiFi"
        self.firmware = device.get("firmwareVersionStringFromDevice")
        uid = str(device["uniqueIdentifier"]).zfill(6)
        self._topic_in = f"{TOPIC_BASE}/I/{uid}"
        self._topic_out = f"{TOPIC_BASE}/O/{uid}"
        self.items: dict[int, bytes] = {}
        # Programy podle čísla (1–9), čtené z termostatu: název a týdenní rozvrh.
        self.programs: dict[int, str] = {}
        self.schedules: dict[int, dict[str, list[tuple[str, float]]]] = {}
        self.connected = False
        self.last_seen: datetime | None = None
        self._listeners: list[Callable[[], None]] = []
        # Čekající zápisy: typ položky → (očekávaná data, nebo None = stačí jakákoli odpověď; událost).
        self._pending: dict[int, tuple[bytes | None, asyncio.Event]] = {}
        self._write_lock = asyncio.Lock()
        client_id = "HA_" + "".join(random.choices(string.ascii_letters + string.digits, k=18))
        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, transport="websockets"
        )
        self._client.ws_set_options(path=MQTT_WS_PATH)
        self._client.username_pw_set(f"{TOPIC_BASE}_{uid}", device["mqttPass"])
        self._client.reconnect_delay_set(5, 300)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

    @property
    def status(self) -> bytes | None:
        data = self.items.get(ITEM_STATUS)
        return data if data and len(data) >= 8 else None

    @property
    def online(self) -> bool:
        """Spojení s brokerem a čerstvá odpověď termostatu."""
        if not self.connected or self.last_seen is None:
            return False
        return (dt_util.utcnow() - self.last_seen).total_seconds() < OFFLINE_SECONDS

    @property
    def boiler_minutes(self) -> int | None:
        """Doba provozu kotle v minutách (odpověď 00 57 16 = 87 h 22 min)."""
        data = self.items.get(ITEM_BOILER_HOURS)
        if not data or len(data) < 3:
            return None
        return int.from_bytes(data[0:2], "big") * 60 + data[2]

    @property
    def firmware_version(self) -> str | None:
        """Verze z položky 0x0003 (14 03 → 14.03, stejně jako v účtu), jinak z účtu."""
        data = self.items.get(ITEM_FIRMWARE)
        if data and len(data) >= 2:
            return f"{data[0]:02x}.{data[1]:02x}"
        return self.firmware

    def setting(self, code: int) -> int | None:
        data = self.items.get(code)
        return data[0] if data and len(data) == 1 else None

    def add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    async def async_start(self) -> None:
        def _connect() -> None:
            self._client.tls_set_context(ssl.create_default_context())
            self._client.connect_async(MQTT_HOST, MQTT_PORT, keepalive=60)
            self._client.loop_start()

        await self.hass.async_add_executor_job(_connect)

    async def async_stop(self) -> None:
        def _stop() -> None:
            self._client.disconnect()
            self._client.loop_stop()

        await self.hass.async_add_executor_job(_stop)

    def request_state(self) -> None:
        self._publish([(READ_FLAG | ITEM_STATUS, b""), (READ_FLAG | ITEM_CLOCK, b"")])

    def request_boiler_hours(self) -> None:
        # Aplikace se ptá položkou 0x0022 s jedním nulovým bajtem; termostat odpoví 0x8022.
        self._publish([(ITEM_BOILER_HOURS, b"\x00")])

    def request_settings(self) -> None:
        # Stejné čtení jako aplikace při otevření nastavení, navíc verze firmwaru.
        self._publish([(READ_FLAG | code, b"") for code in SETTINGS_READ] + [(READ_FLAG | ITEM_FIRMWARE, b"")])

    def sync_clock(self) -> None:
        """Pošle místní čas HA stejně jako aplikace (0x0007 = rr mm dd hh mm ss).

        Se zapnutým NTP si termostat čas bere z internetu a zápis nic nezmění; aplikace ho ale
        posílá při každém otevření, takže je neškodný.
        """
        now = dt_util.now()
        self._publish([(ITEM_CLOCK, bytes([now.year % 100, now.month, now.day, now.hour, now.minute, now.second]))])

    async def async_request_programs(self) -> None:
        for number in range(1, PROGRAM_COUNT + 1):
            self._publish([(READ_FLAG | ITEM_PROGRAM, bytes([number]))])
            await asyncio.sleep(0.3)

    async def async_write_status(self, program: int, mode_byte: int, desired: float) -> None:
        await self._async_write(ITEM_STATUS, bytes([program, mode_byte, int(round(desired * 2))]), echo=False)

    async def async_write_setting(self, code: int, value: int) -> None:
        await self._async_write(code, bytes([value]), echo=True)

    async def _async_write(self, item: int, data: bytes, echo: bool) -> None:
        """Zapíše položku a počká na potvrzení; bez odpovědi to zkusí znovu.

        Nastavení termostat potvrdí stejnou hodnotou (zápis 4B54=58 → odpověď CB54=58),
        zápis stavu potvrdí novým stavem 0x8002.
        """
        if not self.connected:
            raise WriteError("MQTT není připojeno")
        async with self._write_lock:
            for attempt in range(1, WRITE_ATTEMPTS + 1):
                event = asyncio.Event()
                self._pending[item] = (data if echo else None, event)
                self._publish([(item, data)])
                try:
                    await asyncio.wait_for(event.wait(), WRITE_TIMEOUT)
                except TimeoutError:
                    _LOGGER.debug("PT32 %s: zápis %04x bez potvrzení (pokus %d)", self.name, item, attempt)
                    continue
                finally:
                    self._pending.pop(item, None)
                return
        raise WriteError(f"Termostat nepotvrdil zápis položky {item:04x}")

    def _publish(self, items: list[tuple[int, bytes]]) -> None:
        if not self.connected:
            _LOGGER.debug("PT32 %s: MQTT není připojeno, zpráva se neposílá", self.name)
            return
        self._client.publish(self._topic_in, base64.b64encode(build_frame(items)))

    # Zpětná volání paho běží v jeho vlákně; stav se předává do smyčky HA.
    def _on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        if reason_code.is_failure:
            _LOGGER.warning("PT32 %s: MQTT odmítlo připojení: %s", self.name, reason_code)
            return
        client.subscribe(self._topic_out)
        self.hass.loop.call_soon_threadsafe(self._set_connected, True)
        self.hass.loop.call_soon_threadsafe(lambda: self.hass.async_create_task(self._after_connect()))

    def _on_disconnect(self, client, userdata, flags, reason_code, properties) -> None:
        self.hass.loop.call_soon_threadsafe(self._set_connected, False)

    def _on_message(self, client, userdata, msg) -> None:
        try:
            frame = base64.b64decode(msg.payload, validate=True)
        except ValueError:
            return
        items = parse_frame(frame)
        if items:
            self.hass.loop.call_soon_threadsafe(self._update, items)

    async def _after_connect(self) -> None:
        await asyncio.sleep(1)
        self.request_state()
        await asyncio.sleep(1)
        self.request_boiler_hours()
        await asyncio.sleep(1)
        self.request_settings()
        await asyncio.sleep(1)
        self.sync_clock()
        await asyncio.sleep(1)
        await self.async_request_programs()

    @callback
    def _set_connected(self, value: bool) -> None:
        self.connected = value
        self.notify()

    @callback
    def _update(self, items: dict[int, bytes]) -> None:
        self.last_seen = dt_util.utcnow()
        for item, data in items.items():
            pending = self._pending.get(item)
            if pending and (pending[0] is None or pending[0] == data):
                pending[1].set()
        program = items.pop(ITEM_PROGRAM, None)
        if program and len(program) > PROGRAM_NAME_LEN:
            # Data programu: [číslo][týdenní rozvrh…][název 16 B, doplněný nulami nebo mezerami].
            name = program[-PROGRAM_NAME_LEN:].split(b"\x00")[0].decode("cp1250", "replace").strip()
            self.programs[program[0]] = name or f"Program {program[0]:03d}"
            self.schedules[program[0]] = decode_schedule(program[1:-PROGRAM_NAME_LEN])
        self.items.update(items)
        self.notify()

    @callback
    def notify(self) -> None:
        for listener in list(self._listeners):
            listener()
