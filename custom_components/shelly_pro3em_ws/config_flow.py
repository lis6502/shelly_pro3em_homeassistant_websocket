"""Config flow."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_HOST, DOMAIN


class ShellyPro3EmWsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            info, err = await self._probe(host)
            if err:
                errors["base"] = err
            else:
                await self.async_set_unique_id(info["id"])
                self._abort_if_unique_id_configured()
                title = info.get("name") or info["id"]
                return self.async_create_entry(
                    title=title,
                    data={CONF_HOST: host, "device_id": info["id"], "mac": info.get("mac")},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
        )

    async def _probe(self, host: str) -> tuple[dict[str, Any] | None, str | None]:
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(f"http://{host}/shelly", timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    return None, "cannot_connect"
                info = await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
            return None, "cannot_connect"

        if info.get("app") != "Pro3EM" and not str(info.get("id", "")).startswith("shellypro3em"):
            return None, "not_pro3em"
        return info, None
