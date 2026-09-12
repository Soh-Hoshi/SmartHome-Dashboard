#!/usr/bin/env python3
"""
Thread-safe & Atomic State Management for SmartHome Dashboard
Provides Single Source of Truth for state.json with mutex lock and atomic write.
"""
import os
import json
import threading
import tempfile

DIRECTORY = os.path.dirname(os.path.realpath(__file__))
STATE_FILE = os.path.join(DIRECTORY, 'state.json')

_state_lock = threading.RLock()

DEFAULT_STATE = {
    "acMode": "cool",
    "acTemp": 25,
    "acFan": "auto",
    "heaterMode": "off",
    "heaterTemp": 22,
    "heaterEco": False,
    "heaterPower": 2,
    "lightOn": False,
    "lightFull": False,
    "lightNight": False,
    "cleanerStatus": "standby",
    "cleanerPlay": False,
    "usbPower": False,
    "pcOnline": False,
    "pcOs": "オフライン"
}

def load_state() -> dict:
    """スレッドセーフに state.json を読み込み、デフォルト値とマージして返す"""
    with _state_lock:
        state = dict(DEFAULT_STATE)
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        state.update(data)
            except Exception as e:
                print(f"[StateManager Load Error] {e}")
        return state

def save_state(new_state: dict) -> dict:
    """
    スレッドセーフかつアトミックに state.json へ書き込む。
    一時ファイルへ書き出してから os.replace することで、同時読み書きによるファイル破損を完全防止。
    """
    with _state_lock:
        current = load_state()
        current.update(new_state)

        dir_name = os.path.dirname(STATE_FILE)
        try:
            with tempfile.NamedTemporaryFile('w', dir=dir_name, delete=False, encoding='utf-8') as tf:
                json.dump(current, tf, indent=2, ensure_ascii=False)
                temp_name = tf.name
            os.replace(temp_name, STATE_FILE)
        except Exception as e:
            print(f"[StateManager Save Error] {e}")
            try:
                with open(STATE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(current, f, indent=2, ensure_ascii=False)
            except Exception as fe:
                print(f"[StateManager Direct Write Error] {fe}")
        return current

def update_state(**kwargs) -> dict:
    """キー・バリュー形式で部分更新"""
    return save_state(kwargs)

if __name__ == '__main__':
    print("Testing StateManager...")
    st = load_state()
    print("Initial State:", st)
    st = update_state(acTemp=25)
    print("Updated State:", st)
