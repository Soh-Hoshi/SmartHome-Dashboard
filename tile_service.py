#!/usr/bin/env python3
"""
Real-Time Dynamic Tile Key Tracker Service
Monitors BLE advertisements for Tile tags dynamically.
Tile tags use Resolvable Private Addresses (RPA) which rotate periodically.
This service automatically discovers and tracks all devices broadcasting the Tile UUID:
0000feed-0000-1000-8000-00805f9b34fb (Tile, Inc.).
"""

import time
import subprocess
import threading
import datetime
import re
import os
import json

TILE_UUID_PREFIX = "0000feed"
GRACE_PERIOD_SECONDS = 60

_lock = threading.Lock()
_known_tile_macs = {"18:26:88:50:69:91", "30:F7:75:1F:0E:20", "2B:E6:76:67:69:74", "1A:95:48:B6:32:D7"}
_state = {
    "in_home": True,
    "last_seen": time.time(),
    "rssi": -54,
    "mac": "2B:E6:76:67:69:74",
    "last_check": time.time(),
    "status_text": "検知",
    "device_name": "鍵（Tile）"
}

def _refresh_tile_macs():
    """BlueZデバイスキャッシュからTile UUID (0000feed) を持つMACを自動検出して登録"""
    global _known_tile_macs
    try:
        p = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        p.stdin.write('devices\nexit\n')
        out, _ = p.communicate(timeout=3)
        
        for line in out.splitlines():
            if 'Device ' in line:
                parts = line.split()
                if len(parts) >= 2:
                    mac = parts[1]
                    if mac not in _known_tile_macs:
                        # info を確認
                        p_info = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                        p_info.stdin.write(f'info {mac}\nexit\n')
                        info_out, _ = p_info.communicate(timeout=1.5)
                        if TILE_UUID_PREFIX in info_out.lower() or 'tile, inc.' in info_out.lower():
                            with _lock:
                                _known_tile_macs.add(mac)
    except Exception as e:
        print(f"[Tile Dynamic Discovery Notice] {e}")

def _tile_live_scanner():
    global _state, _known_tile_macs
    cycle_count = 0

    while True:
        try:
            # 5サイクル（約30秒）ごとに未知のTile MACアドレス探索を実行
            if cycle_count % 5 == 0:
                _refresh_tile_macs()
            cycle_count += 1

            # 5秒間ライブBLEスキャンを実行
            p = subprocess.Popen(
                ['bluetoothctl'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            p.stdin.write('scan on\n')
            p.stdin.flush()
            time.sleep(4.5)
            p.stdin.write('scan off\nexit\n')
            p.stdin.flush()
            out, _ = p.communicate(timeout=3)

            latest_rssi = None
            detected_mac = None
            detected_now = False

            # スキャンログの中から Tile のライブ受信パケットを検証
            with _lock:
                current_macs = set(_known_tile_macs)

            for line in out.splitlines():
                line_upper = line.upper()
                for target_mac in current_macs:
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

        time.sleep(1.5)

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
    print(f"Starting Dynamic Tile live scanner...")
    start_tile_service()
    for _ in range(8):
        time.sleep(1)
        st = get_tile_status()
        print(f"Status: {st['status_text']} | in_home: {st['in_home']} | RSSI: {st['rssi']} | MAC: {st['mac']}")
