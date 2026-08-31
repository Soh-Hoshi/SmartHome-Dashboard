#!/usr/bin/env python3
"""
Tile Key Tracker Presence Service
Monitors whether the physical key tagged with Tile is inside the home vs outside in the mailbox.
Target MAC: 30:F7:75:1F:0E:20 (Tile, Inc. UUID: 0000feed-0000-1000-8000-00805f9b34fb)
"""

import time
import subprocess
import threading
import datetime
import re
import os
import json

TARGET_TILE_MAC = "30:F7:75:1F:0E:20"
# ポスト（室外）にある時は電波が届かない。室内に持ち帰ると電波を受信する。
# 120秒（2分）以上電波が途絶えたら「ポスト保管中（室外）」と判定。
GRACE_PERIOD_SECONDS = 120

_lock = threading.Lock()
_state = {
    "in_home": True,
    "last_seen": time.time(),
    "rssi": -46,
    "mac": TARGET_TILE_MAC,
    "last_check": time.time(),
    "status_text": "室内で検知（置き忘れ注意）",
    "device_name": "鍵（Tile）"
}

def probe_tile():
    """
    bluetoothctl info または devices で Tile の直近の RSSI / 受信を確認
    """
    try:
        # bluetoothctl info で直近のステータスを取得
        p = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        p.stdin.write(f'info {TARGET_TILE_MAC}\nexit\n')
        out, _ = p.communicate(timeout=2.5)

        rssi = None
        has_tile = False

        for line in out.splitlines():
            line_str = line.strip()
            if 'Tile, Inc.' in line_str or '0000feed' in line_str or TARGET_TILE_MAC in line_str:
                has_tile = True
            if line_str.startswith('RSSI:'):
                m = re.search(r'\(-?(\d+)\)', line_str)
                if m:
                    rssi = -int(m.group(1))

        # RSSI が存在し、電波が届いていれば室内
        if rssi is not None and rssi > -90:
            return True, rssi
        return has_tile and (rssi is not None), rssi
    except Exception as e:
        return False, None

def _tile_scanner_worker():
    global _state
    while True:
        try:
            # 5秒間 BLE scan を実行して周囲の最新 RSSI を拾う
            p = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            p.stdin.write('scan on\n')
            p.stdin.flush()
            time.sleep(4)
            p.stdin.write('scan off\nexit\n')
            p.stdin.flush()
            out, _ = p.communicate(timeout=3)

            # スキャン結果から TARGET_TILE_MAC の最新 RSSI を抽出
            latest_rssi = None
            for line in out.splitlines():
                if TARGET_TILE_MAC in line and 'RSSI:' in line:
                    m = re.search(r'RSSI:.*?\(-?(\d+)\)', line)
                    if m:
                        latest_rssi = -int(m.group(1))

            if latest_rssi is None:
                # info コマンドで再確認
                detected, info_rssi = probe_tile()
                if detected:
                    latest_rssi = info_rssi

            now = time.time()
            with _lock:
                _state["last_check"] = now
                if latest_rssi is not None:
                    _state["last_seen"] = now
                    _state["rssi"] = latest_rssi
                    _state["in_home"] = True
                    _state["status_text"] = "室内で検知（置き忘れ注意）"
                else:
                    # 猶予期間を超えて電波が届かなければ「ポスト保管中（室外）」
                    if now - _state["last_seen"] > GRACE_PERIOD_SECONDS:
                        _state["in_home"] = False
                        _state["status_text"] = "ポスト保管中（室外）"
                    else:
                        _state["in_home"] = True
                        _state["status_text"] = "室内で検知（置き忘れ注意）"
        except Exception as e:
            print(f"[Tile Service Error] {e}")

        time.sleep(8)

def start_tile_service():
    t = threading.Thread(target=_tile_scanner_worker, daemon=True, name="TileWorker")
    t.start()

def get_tile_status():
    with _lock:
        last_seen_dt = datetime.datetime.fromtimestamp(_state["last_seen"])
        return {
            "in_home": _state["in_home"],
            "status_text": _state["status_text"],
            "mac": _state["mac"],
            "rssi": _state["rssi"],
            "last_seen_epoch": _state["last_seen"],
            "last_seen_str": last_seen_dt.strftime("%H:%M:%S"),
            "last_seen_formatted": last_seen_dt.strftime("%Y/%m/%d %H:%M:%S"),
            "device_name": _state["device_name"]
        }

if __name__ == '__main__':
    print(f"Testing Tile probe for {TARGET_TILE_MAC}...")
    detected, rssi = probe_tile()
    print(f"Probe result: {'Detected (In Home)' if detected else 'Not Detected'}, RSSI: {rssi} dBm")
    start_tile_service()
    time.sleep(5)
    print("Tile status:", json.dumps(get_tile_status(), indent=2, ensure_ascii=False))
