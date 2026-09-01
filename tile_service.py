#!/usr/bin/env python3
"""
Real-Time Tile Key Tracker Service
Monitors live BLE advertisements for Tile tags.
Bypasses BlueZ static device cache to ensure real-time presence detection.
"""

import time
import subprocess
import threading
import datetime
import re
import os
import json

KNOWN_TILE_MACS = ["18:26:88:50:69:91", "30:F7:75:1F:0E:20"]
# 電波が途絶えてから45秒で「検知なし（ポスト保管）」に切り替え
GRACE_PERIOD_SECONDS = 45

_lock = threading.Lock()
_state = {
    "in_home": False,
    "last_seen": 0,
    "rssi": None,
    "mac": KNOWN_TILE_MACS[0],
    "last_check": time.time(),
    "status_text": "検知なし",
    "device_name": "鍵（Tile）"
}

def _tile_live_scanner():
    global _state
    while True:
        try:
            # 4秒間ライブBLEスキャンを実行
            p = subprocess.Popen(
                ['bluetoothctl'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            p.stdin.write('scan on\n')
            p.stdin.flush()
            time.sleep(3.5)
            p.stdin.write('scan off\nexit\n')
            p.stdin.flush()
            out, _ = p.communicate(timeout=3)

            latest_rssi = None
            detected_mac = None
            detected_now = False

            # スキャンログの中から Tile のライブ受信パケットを検証
            for line in out.splitlines():
                line_upper = line.upper()
                # 既知の MAC アドレスチェック
                for target_mac in KNOWN_TILE_MACS:
                    if target_mac.upper() in line_upper:
                        detected_now = True
                        detected_mac = target_mac
                        if 'RSSI:' in line_upper:
                            m = re.search(r'RSSI:.*?\(-?(\d+)\)', line)
                            if m:
                                latest_rssi = -int(m.group(1))

            now = time.time()
            with _lock:
                _state["last_check"] = now
                if detected_now:
                    _state["last_seen"] = now
                    _state["in_home"] = True
                    _state["status_text"] = "検知"
                    if detected_mac:
                        _state["mac"] = detected_mac
                    if latest_rssi is not None:
                        _state["rssi"] = latest_rssi
                else:
                    # 猶予期間を超えてパケットが届かなければ「検知なし」
                    if now - _state["last_seen"] > GRACE_PERIOD_SECONDS:
                        _state["in_home"] = False
                        _state["status_text"] = "検知なし"
                        _state["rssi"] = None
                    else:
                        _state["in_home"] = True
                        _state["status_text"] = "検知"
        except Exception as e:
            print(f"[Tile Service Error] {e}")

        time.sleep(2)

def start_tile_service():
    t = threading.Thread(target=_tile_live_scanner, daemon=True, name="TileLiveScanner")
    t.start()

def get_tile_status():
    with _lock:
        last_seen_str = "--:--:--"
        last_seen_formatted = "--"
        if _state["last_seen"] > 0:
            last_seen_dt = datetime.datetime.fromtimestamp(_state["last_seen"])
            last_seen_str = last_seen_dt.strftime("%H:%M:%S")
            last_seen_formatted = last_seen_dt.strftime("%Y/%m/%d %H:%M:%S")

        return {
            "in_home": _state["in_home"],
            "status_text": _state["status_text"],
            "mac": _state["mac"],
            "rssi": _state["rssi"],
            "last_seen_epoch": _state["last_seen"],
            "last_seen_str": last_seen_str,
            "last_seen_formatted": last_seen_formatted,
            "device_name": _state["device_name"]
        }

if __name__ == '__main__':
    print(f"Starting Tile live scanner for {KNOWN_TILE_MACS}...")
    start_tile_service()
    for _ in range(8):
        time.sleep(1)
        st = get_tile_status()
        print(f"Status: {st['status_text']} | in_home: {st['in_home']} | RSSI: {st['rssi']} | MAC: {st['mac']}")
