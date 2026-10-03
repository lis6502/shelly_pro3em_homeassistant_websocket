# Shelly Pro 3EM – WebSocket (no auth)

Custom integration for Home Assistant that reads a **Shelly Pro 3EM** you can't log into
(e.g. a meter installed and password-protected by your energy supplier).
Why? Because not always we own the device.

It does **not** use or need the device password. It opens the device's `/rpc` WebSocket and
listens to the status notifications (`NotifyStatus`) the device pushes to connected clients.
It is **read-only** – it never changes any setting on the meter.

## What you get

| Source | Interval | Sensors |
|---|---|---|
| `em:0` | ~15 s | Active / apparent power, current, voltage, power factor, frequency – per phase and total |
| `emdata:0` | ~60 s | Energy imported / exported (kWh) – total and per phase |

`Total energy imported` and `Total energy exported` are `total_increasing` energy sensors and can be
added directly to the **Energy dashboard** (Grid consumption / Return to grid).
Per-phase energy, apparent power, PF and frequency sensors are disabled by default.

## Installation

### HACS (custom repository)
1. HACS → ⋮ → *Custom repositories* → add this repo URL, category **Integration**.
2. Install **Shelly Pro 3EM (WebSocket, no auth)** and restart Home Assistant.

### Manual
Copy `custom_components/shelly_pro3em_ws` to `/config/custom_components/` and restart Home Assistant.

## Configuration
*Settings → Devices & services → Add integration →* **Shelly Pro 3EM (WebSocket, no auth)**, enter the meter IP.
Give the meter a DHCP reservation so the IP doesn't change.

## Quick check before installing
```bash
python3 -m venv v && v/bin/pip install websockets
v/bin/python - <<'PY'
import asyncio, websockets, json
async def m():
    async with websockets.connect("ws://METER_IP/rpc", origin="http://METER_IP") as ws:
        await ws.send(json.dumps({"id":1,"src":"test","method":"Shelly.GetDeviceInfo"}))
        async for msg in ws: print(msg)
asyncio.run(m())
PY
```
If you see `NotifyStatus` frames with `em:0` (and every minute `emdata:0`), the integration will work.

Tested with firmware 1.4.2 (`auth_en: true`).
