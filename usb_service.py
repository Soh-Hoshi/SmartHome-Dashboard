#!/usr/bin/env python3
"""
USB Switch Service (Sinilink USB via ESPHome Native API)
Directly controls the USB power switch without depending on Home Assistant.
"""

import asyncio
import threading
import time
from aioesphomeapi import APIClient, SwitchState
import state_manager

USB_HOST = "192.168.0.210"
USB_PORT = 6053
USB_KEY = 2653998163
TIMEOUT_SECONDS = 2.5

_lock = threading.Lock()
_last_fetch_time = 0
_cached_state = None

async def _fetch_state_async():
    client = APIClient(USB_HOST, USB_PORT, password='', noise_psk=None)
    try:
        await client.connect(login=True)
        loop = asyncio.get_running_loop()
        fut = loop.create_future()

        def on_state(state):
            if isinstance(state, SwitchState) and state.key == USB_KEY:
                if not fut.done():
                    fut.set_result(state.state)

        client.subscribe_states(on_state)
        res = await asyncio.wait_for(fut, timeout=TIMEOUT_SECONDS)
        return bool(res)
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass

async def _set_power_async(power: bool):
    client = APIClient(USB_HOST, USB_PORT, password='', noise_psk=None)
    try:
        await client.connect(login=True)
        loop = asyncio.get_running_loop()
        fut = loop.create_future()

        def on_state(state):
            if isinstance(state, SwitchState) and state.key == USB_KEY:
                if not fut.done():
                    fut.set_result(state.state)

        client.subscribe_states(on_state)
        client.switch_command(key=USB_KEY, state=power)
        try:
            res = await asyncio.wait_for(fut, timeout=TIMEOUT_SECONDS)
            return bool(res)
        except asyncio.TimeoutError:
            return power
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass

def get_usb_power(force_refresh=False) -> bool:
    global _last_fetch_time, _cached_state
    now = time.time()
    with _lock:
        if not force_refresh and _cached_state is not None and (now - _last_fetch_time < 3.0):
            return _cached_state

        try:
            st = asyncio.run(_fetch_state_async())
            _cached_state = st
            _last_fetch_time = now
            state_manager.update_state(usbPower=st)
            return st
        except Exception as e:
            print(f"[USB Service] Fetch error: {e}")
            saved = state_manager.load_state().get("usbPower", False)
            return saved

def set_usb_power(power: bool) -> bool:
    global _last_fetch_time, _cached_state
    with _lock:
        try:
            st = asyncio.run(_set_power_async(power))
            _cached_state = st
            _last_fetch_time = time.time()
            state_manager.update_state(usbPower=st)
            return st
        except Exception as e:
            print(f"[USB Service] Set power error: {e}")
            state_manager.update_state(usbPower=power)
            _cached_state = power
            return power

def toggle_usb_power() -> bool:
    current = get_usb_power(force_refresh=True)
    return set_usb_power(not current)

if __name__ == '__main__':
    print("Fetching USB switch state...")
    st = get_usb_power(force_refresh=True)
    print("USB Switch State:", "ON" if st else "OFF")
