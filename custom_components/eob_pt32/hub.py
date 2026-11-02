"""Spojení s termostatem PT32 WiFi přes cloud Elektrobock (REST + MQTT přes WebSocket)."""

from __future__ import annotations

import asyncio
import base64
import logging
import random
import ssl
import string
from collections.abc import Callable

import aiohttp
import paho.mqtt.client as mqtt

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_BASE,
    API_DEVICES,
    API_LOGIN,
    DEVICE_TYPE_PT32_WIFI,
    FRAME_REQUEST,
    FRAME_RESPONSE,
    ITEM_CLOCK,
    ITEM_STATUS,
    LEN_MASK,
    MQTT_HOST,
    MQTT_PORT,
    MQTT_WS_PATH,
    READ_FLAG,
    TOPIC_BASE,
)

_LOGGER = logging.getLogger(__name__)


class AuthError(Exception):
    """Špatné přihlašovací údaje."""


async def async_fetch_devices(hass: HomeAssistant, username: str, password: str) -> list[dict]:
    """Přihlásí se a vrátí termostaty PT32 WiFi v účtu."""
    session = async_get_clientsession(hass)
    async with session.post(API_BASE + API_LOGIN, json={"userName": username, "password": password}) as resp:
        if resp.status in (400, 401, 403):
            raise AuthError
        resp.raise_for_status()
        account = await resp.json()
    headers = {"Authorization": f"Bearer {account['authToken']}"}
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
        self.connected = False
        self._listeners: list[Callable[[], None]] = []
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

    def write_status(self, mode_byte: int, desired: float) -> None:
        self._publish([(ITEM_STATUS, bytes([0x01, mode_byte, int(round(desired * 2))]))])

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
        self.request_state_soon()

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

    def request_state_soon(self) -> None:
        self.hass.loop.call_soon_threadsafe(lambda: self.hass.async_create_task(self._delayed_request()))

    async def _delayed_request(self) -> None:
        await asyncio.sleep(1)
        self.request_state()

    @callback
    def _set_connected(self, value: bool) -> None:
        self.connected = value
        self._notify()

    @callback
    def _update(self, items: dict[int, bytes]) -> None:
        self.items.update(items)
        self._notify()

    @callback
    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()
