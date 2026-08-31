#!/usr/bin/env python3
"""
Eufy RoboVac G30 Hybrid Local Tuya Controller
"""

import sys
import os
import json
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import tinytuya

_LOGGER = logging.getLogger(__name__)

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

def load_eufy_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return cfg.get("eufy", {})
        except Exception as e:
            _LOGGER.error(f"Error loading config.json: {e}")
    return {}

class EufyG30Client:
    def __init__(self, config=None):
        cfg = config or load_eufy_config()
        self.dev_id = cfg.get("dev_id", "ebbcd582d5428c96acf5ts")
        self.local_key = cfg.get("local_key", "+tB=i{nIUWtM|A]1")
        self.ip = cfg.get("ip", "192.168.0.233")
        self.version = cfg.get("version", 3.4)
        self.device = None
        self._init_device()

    def _init_device(self):
        try:
            self.device = tinytuya.OutletDevice(
                dev_id=self.dev_id,
                address=self.ip,
                local_key=self.local_key,
                version=self.version
            )
            self.device.set_socketPersistent(False)
            self.device.set_socketTimeout(3.0)
        except Exception as e:
            _LOGGER.error(f"Failed to init Tuya device: {e}")
            self.device = None

    def get_status(self):
        """Fetch current status and parse DPS into human-friendly format."""
        if not self.device:
            self._init_device()
        try:
            res = self.device.status()
            if not res or "dps" not in res:
                return {"success": False, "error": res.get("Error", "No DPS data")}
            
            dps = res["dps"]
            
            # DPS Mapping
            # 1: Power (bool)
            # 2: Play/Pause (bool)
            # 5: Mode ('auto', 'Edge', 'Spot', 'SmallRoom', 'Nosweep')
            # 15: Status ('Running', 'Charging', 'standby', 'Sleeping', 'Recharge', 'completed')
            # 101: Go Home (bool)
            # 102: Speed ('Standard', 'Boost_IQ', 'Max', 'No_suction')
            # 104: Battery (int 0-100)
            # 106: Error Code (0 = OK)
            # 107: Find Me (bool)
            # 109: Clean duration (seconds)
            # 110: Clean area (sqm)
            # 131: Mop attached (bool)
            
            clean_sec = dps.get("109", 0)
            clean_min = round(clean_sec / 60) if isinstance(clean_sec, (int, float)) else 0

            raw_status = str(dps.get("15", "standby")).strip().lower()
            mode = str(dps.get("5", "auto")).strip()
            pause_state = str(dps.get("122", "")).strip()

            # DPS 15 の真のステータス判定
            # "running": 清掃中
            # "recharge": 帰還中
            # "charging": 充電中
            # "completed": 充電完了
            # "standby": 一時停止 / 待機中
            # "sleeping": スリープ
            if raw_status == "running":
                final_status = "running"
            elif raw_status == "recharge":
                final_status = "recharge"
            elif raw_status == "charging":
                final_status = "charging"
            elif raw_status == "completed":
                final_status = "completed"
            elif raw_status == "sleeping":
                final_status = "sleeping"
            else:
                # standby
                final_status = "standby"

            is_running = (final_status == "running")

            return {
                "success": True,
                "connected": True,
                "power": dps.get("1", False),
                "play": is_running,
                "mode": mode,
                "status": final_status,
                "raw_status": dps.get("15", "standby"),
                "pause_state": pause_state,
                "go_home": bool(dps.get("101", False)),
                "speed": dps.get("102", "Standard"),
                "battery": dps.get("104", 0),
                "error_code": dps.get("106", 0),
                "find_me": dps.get("107", False),
                "clean_time_min": clean_min,
                "clean_time_sec": clean_sec,
                "clean_area": dps.get("110", 0),
                "mop_attached": dps.get("131", False),
                "raw_dps": dps
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def play(self):
        """Start or resume cleaning (DPS 5: auto, DPS 2: True)."""
        self._set_dp(5, "auto")
        return self._set_dp(2, True)

    def pause(self):
        """Pause cleaning (DPS 2: False)."""
        return self._set_dp(2, False)

    def return_to_dock(self):
        """Send vacuum back to charging dock (DPS 101: True)."""
        return self._set_dp(101, True)

    def set_clean_speed(self, speed):
        """Set suction speed: 'Standard', 'Boost_IQ', 'Max', 'No_suction'."""
        valid_speeds = ["Standard", "Boost_IQ", "Max", "No_suction"]
        if speed not in valid_speeds:
            return {"success": False, "error": f"Invalid speed. Choose from {valid_speeds}"}
        return self._set_dp(102, speed)

    def set_work_mode(self, mode):
        """Set cleaning mode: 'auto', 'Edge', 'Spot', 'SmallRoom'."""
        valid_modes = ["auto", "Edge", "Spot", "SmallRoom"]
        if mode not in valid_modes:
            return {"success": False, "error": f"Invalid mode. Choose from {valid_modes}"}
        return self._set_dp(5, mode)

    def find_robot(self):
        """Trigger beep on robot (DPS 103: True, then False after 3s)."""
        res = self._set_dp(103, True)
        
        def auto_off():
            import time
            time.sleep(3.5)
            try:
                self._set_dp(103, False)
            except Exception:
                pass
                
        import threading
        threading.Thread(target=auto_off, daemon=True).start()
        return res

    def _set_dp(self, dp_id, value):
        if not self.device:
            self._init_device()
        try:
            res = self.device.set_value(int(dp_id), value)
            return {"success": True, "result": res}
        except Exception as e:
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    client = EufyG30Client()
    print("Testing config load & status fetch...")
    status = client.get_status()
    import pprint
    pprint.pprint(status)
