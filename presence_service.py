#!/usr/bin/env python3
"""
Presence Detection Service
Detects whether the target device (User's smartphone) is at home via IP/ARP ping.
Target IP: 192.168.0.30
Target MAC: 72:58:BA:C7:40:FA
"""

import time
import subprocess
import threading
import datetime
import re
import os
import json

TARGET_IP = "192.168.0.30"
TARGET_MAC = "72:58:ba:c7:40:fa"
GRACE_PERIOD_SECONDS = 180  # 3分間のスリープ猶予（スマホの省電力スリープ誤判定防止）

_lock = threading.Lock()
_state = {
    "is_home": True,
    "last_seen": time.time(),
    "ip": TARGET_IP,
    "mac": TARGET_MAC.upper(),
    "last_check": time.time(),
    "status_text": "在宅中"
}

def probe_device():
    """
    対象デバイスが存在するか高速プローブ（Ping + ARPテーブル検証）
    """
    # 1. Ping プローブ
    ping_ok = False
    try:
        res = subprocess.run(
            ["ping", "-c", "1", "-W", "1", TARGET_IP],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if res.returncode == 0:
            ping_ok = True
    except Exception:
        pass

    # 2. ARP / Neigh テーブル確認
    arp_ok = False
    try:
        res = subprocess.run(
            ["ip", "neigh", "show", TARGET_IP],
            capture_output=True,
            text=True,
            timeout=2
        )
        output = res.stdout.lower()
        if TARGET_MAC in output and ("reachable" in output or "delay" in output or "stale" in output):
            arp_ok = True
    except Exception:
        pass

    return ping_ok or arp_ok

def _presence_worker():
    global _state
    while True:
        try:
            detected = probe_device()
            now = time.time()
            with _lock:
                _state["last_check"] = now
                if detected:
                    _state["last_seen"] = now
                    _state["is_home"] = True
                    _state["status_text"] = "在宅中"
                else:
                    # 猶予期間を超えて応答がない場合は「外出中」
                    if now - _state["last_seen"] > GRACE_PERIOD_SECONDS:
                        _state["is_home"] = False
                        _state["status_text"] = "外出中"
                    else:
                        _state["is_home"] = True
                        _state["status_text"] = "在宅中"
        except Exception as e:
            print(f"[Presence Service Error] {e}")

        time.sleep(10)

def start_presence_service():
    t = threading.Thread(target=_presence_worker, daemon=True, name="PresenceWorker")
    t.start()

def get_presence_status():
    with _lock:
        last_seen_dt = datetime.datetime.fromtimestamp(_state["last_seen"])
        return {
            "is_home": _state["is_home"],
            "status_text": _state["status_text"],
            "ip": _state["ip"],
            "mac": _state["mac"],
            "last_seen_epoch": _state["last_seen"],
            "last_seen_str": last_seen_dt.strftime("%H:%M:%S"),
            "last_seen_formatted": last_seen_dt.strftime("%Y/%m/%d %H:%M:%S"),
            "device_name": "スマートフォン"
        }

if __name__ == '__main__':
    print("Testing device presence probe for 192.168.0.30...")
    detected = probe_device()
    print(f"Probe result: {'Detected (At Home)' if detected else 'Not Detected'}")
    start_presence_service()
    time.sleep(1)
    print("Presence status:", json.dumps(get_presence_status(), indent=2, ensure_ascii=False))
