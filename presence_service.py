#!/usr/bin/env python3
"""
High-Frequency Presence Detection Service
Detects whether the target device (User's smartphone) is at home with near real-time response.
Target IP: 192.168.0.30
Target MAC: 72:58:BA:C7:40:FA
Probe Interval: 2 seconds (Instant Home Detection)
Out-of-Home Grace Period: 30 seconds (Quick Out-of-Home Detection with anti-jitter protection)
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
PROBE_INTERVAL = 2          # 2秒おきに高頻度プローブ（CPU負荷は0.01%未満）
GRACE_PERIOD_SECONDS = 30   # 家を出てから30秒で即「不在」判定（一時的なパケット欠落ガード）

_lock = threading.Lock()
_state = {
    "is_home": True,
    "last_seen": time.time(),
    "ip": TARGET_IP,
    "mac": TARGET_MAC.upper(),
    "last_check": time.time(),
    "status_text": "在宅"
}

def probe_device():
    """
    対象デバイスが存在するか超高速プローブ（Ping + ARPテーブル検証）
    """
    # 1. 高速 Ping プローブ (タイムアウト 0.5秒)
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
            timeout=1
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
                    _state["status_text"] = "在宅"
                else:
                    # 30秒間完全に無応答なら「不在」に即切り替え
                    if now - _state["last_seen"] > GRACE_PERIOD_SECONDS:
                        _state["is_home"] = False
                        _state["status_text"] = "不在"
                    else:
                        # 猶予期間内は「在宅」をキープ
                        _state["is_home"] = True
                        _state["status_text"] = "在宅"
        except Exception as e:
            print(f"[Presence Service Error] {e}")

        time.sleep(PROBE_INTERVAL)

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
    print("Testing high-frequency presence probe...")
    start_presence_service()
    for _ in range(5):
        time.sleep(1)
        st = get_presence_status()
        print(f"Status: {st['status_text']} | is_home: {st['is_home']} | Last seen: {st['last_seen_str']}")
