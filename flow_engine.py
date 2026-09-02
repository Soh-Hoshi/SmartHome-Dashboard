#!/usr/bin/env python3
"""
Smart Scene & Automation Execution Engine
Directly executes intelligent smart home scenes based on live weather (feels_like) and presence,
generating clean, natural voice assistant responses.
"""

import os
import json
import threading
import weather_service

SCENES_CONFIG_PATH = "/home/soh/dashboard/scenes_config.json"
AUTOMATIONS_CONFIG_PATH = "/home/soh/dashboard/automations_config.json"
STATE_FILE = "/home/soh/dashboard/state.json"

_lock = threading.Lock()

def load_scenes():
    """scenes_config.json からシーン一覧をロード"""
    with _lock:
        if os.path.exists(SCENES_CONFIG_PATH):
            try:
                with open(SCENES_CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[FlowEngine Load Scenes Error] {e}")
        return []

def load_automations():
    """automations_config.json からオートメーション一覧をロード"""
    with _lock:
        if os.path.exists(AUTOMATIONS_CONFIG_PATH):
            try:
                with open(AUTOMATIONS_CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[FlowEngine Load Automations Error] {e}")
        return []

def execute_smart_hvac(send_api_fn=None, sleep_mode=False):
    """
    木月のリアルタイム体感温度（feels_like）に基づく空調（エアコン/ヒーター）自動判定・制御
    sleep_mode=True の場合は就寝冷房27℃、通常時は冷房26℃
    """
    wdata = weather_service.get_weather_data()
    feels_like = wdata.get('feels_like', wdata.get('temp', 24.0))
    target_ac_temp = 27 if sleep_mode else 26

    # 体感温度 24.0℃以上 ──▶ エアコン冷房
    if feels_like >= 24.0:
        hvac_type = 'ac'
        temp = target_ac_temp
        if send_api_fn:
            send_api_fn('/api/ac', {'mode': 'cool', 'temp': temp, 'fan_mode': 'auto'})
            send_api_fn('/api/heater', {'action': 'off'})
    # 体感温度 19.0℃以下 ──▶ ヒーターON
    elif feels_like <= 19.0:
        hvac_type = 'heater'
        temp = None
        if send_api_fn:
            send_api_fn('/api/heater', {'action': 'on'})
            send_api_fn('/api/ac', {'mode': 'off'})
    # 快適（20.0〜23.9℃） ──▶ 空調OFF（節電）
    else:
        hvac_type = 'none'
        temp = None
        if send_api_fn:
            send_api_fn('/api/ac', {'mode': 'off'})
            send_api_fn('/api/heater', {'action': 'off'})

    return {
        "hvac": hvac_type,
        "temp": temp,
        "feels_like": feels_like
    }

def execute_scene(scene_id, send_api_fn=None):
    """
    シーンを実行し、結果メッセージを返す
    """
    if scene_id in ("morning", "おはよう"):
        if send_api_fn:
            send_api_fn('/api/light', {'action': 'on'})
        hvac = execute_smart_hvac(send_api_fn, sleep_mode=False)
        fl = hvac['feels_like']
        if hvac['hvac'] == 'ac':
            msg = f"おはようございます。照明を点灯し、体感温度{fl:.1f}℃のためエアコンを冷房26℃で運転開始しました。"
        elif hvac['hvac'] == 'heater':
            msg = f"おはようございます。照明を点灯し、体感温度{fl:.1f}℃のためヒーターをオンにしました。"
        else:
            msg = f"おはようございます。照明を点灯しました。体感温度{fl:.1f}℃で快適なため空調は停止のままです。"
        return {"success": True, "scene_id": "morning", "name": "おはよう", "message": msg}

    if scene_id in ("goodnight", "おやすみ"):
        if send_api_fn:
            send_api_fn('/api/light', {'action': 'off'})
        hvac = execute_smart_hvac(send_api_fn, sleep_mode=True)
        fl = hvac['feels_like']
        if hvac['hvac'] == 'ac':
            msg = f"おやすみなさい。照明を消灯し、体感温度{fl:.1f}℃のため就寝用にエアコンを冷房27℃に設定しました。良い夢を。"
        elif hvac['hvac'] == 'heater':
            msg = f"おやすみなさい。照明を消灯し、体感温度{fl:.1f}℃のためヒーターをオンにしました。良い夢を。"
        else:
            msg = "おやすみなさい。照明と空調をオフにしました。良い夢を。"
        return {"success": True, "scene_id": "goodnight", "name": "おやすみ", "message": msg}

    if scene_id in ("leaving", "いってきます"):
        if send_api_fn:
            send_api_fn('/api/light', {'action': 'off'})
            send_api_fn('/api/ac', {'mode': 'off'})
            send_api_fn('/api/heater', {'action': 'off'})
        return {
            "success": True,
            "scene_id": "leaving",
            "name": "いってきます",
            "message": "いってらっしゃい！すべての照明と空調を停止しました。お気をつけて！"
        }

    if scene_id in ("welcome", "ただいま"):
        wdata = weather_service.get_weather_data()
        is_night = not wdata.get('is_day', True)
        if is_night and send_api_fn:
            send_api_fn('/api/light', {'action': 'on'})

        hvac = execute_smart_hvac(send_api_fn, sleep_mode=False)
        fl = hvac['feels_like']
        light_txt = "日没後のため照明を点灯し、" if is_night else "日没前のため照明はオフのまま、"
        if hvac['hvac'] == 'ac':
            hvac_txt = f"体感温度{fl:.1f}℃のためエアコンを冷房26℃で運転開始しました。"
        elif hvac['hvac'] == 'heater':
            hvac_txt = f"体感温度{fl:.1f}℃のためヒーターをオンにしました。"
        else:
            hvac_txt = "快適な室温のため空調は停止のままです。"
        msg = f"おかえりなさい！{light_txt}{hvac_txt}"
        return {"success": True, "scene_id": "welcome", "name": "ただいま", "message": msg}

    return {"success": False, "message": f"シーン '{scene_id}' が見つかりません。"}
