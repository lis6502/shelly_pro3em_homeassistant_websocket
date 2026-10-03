"""Push coordinator: inbound Shelly /rpc WebSocket."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, EM_KEYS, EMDATA_KEYS

_LOGGER = logging.getLogger(__name__)

HELLO = {
    "id": 1,
    "src": "homeassistant",
    "method": "Shelly.GetDeviceInfo",
}


class ShellyWsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, host: str, device_id: str) -> None:
        super().__init__(hass, _LOGGER, name=f"{DOMAIN}_{host}")
        self.host = host
        self.device_id = device_id
        self.data: dict[str, Any] = {}
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

    async def async_start(self) -> None:
        self._stop.clear()
        self._task = self.hass.async_create_background_task(
            self._run(),
            name=f"{DOMAIN}_ws_{self.host}",
        )

    async def async_stop(self) -> None:
        self._stop.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self) -> None:
        session = async_get_clientsession(self.hass)
        delay = 1.0
        while not self._stop.is_set():
            try:
                await self._listen(session)
                delay = 1.0
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 — keep the socket loop alive
                _LOGGER.warning("WebSocket to %s dropped; retry in %.0fs", self.host, delay, exc_info=True)
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=delay)
                except asyncio.TimeoutError:
                    pass
                delay = min(delay * 2, 60.0)

    async def _listen(self, session: aiohttp.ClientSession) -> None:
        url = f"ws://{self.host}/rpc"
        timeout = aiohttp.ClientTimeout(total=None, sock_connect=10, sock_read=120)
        async with session.ws_connect(
            url,
            heartbeat=30,
            timeout=timeout,
            origin=f"http://{self.host}",
        ) as ws:
            await ws.send_json(HELLO)
            async for msg in ws:
                if self._stop.is_set():
                    break
                if msg.type == aiohttp.WSMsgType.TEXT:
                    self._handle_payload(msg.data)
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    break

    def _handle_payload(self, raw: str) -> None:
        import json

        try:
            frame = json.loads(raw)
        except ValueError:
            return

        if frame.get("method") != "NotifyStatus":
            return
        params = frame.get("params") or {}
        em = params.get("em:0")
        emdata = params.get("emdata:0")
        if not isinstance(em, dict) and not isinstance(emdata, dict):
            return

        changed = False
        merged = dict(self.data)
        for block, keys in ((em, EM_KEYS), (emdata, EMDATA_KEYS)):
            if not isinstance(block, dict):
                continue
            for key in keys:
                if key in block:
                    val = block[key]
                    if merged.get(key) != val:
                        merged[key] = val
                        changed = True
        if "ts" in params:
            merged["ts"] = params["ts"]
        if changed:
            self.async_set_updated_data(merged)
