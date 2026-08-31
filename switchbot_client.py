#!/usr/bin/env python3
"""
SwitchBot OpenAPI v1.1 Client for Dashboard
"""
import os
import time
import uuid
import hmac
import hashlib
import base64
import json
import urllib.request
import urllib.error

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_headers(token: str, secret: str):
    t = str(int(round(time.time() * 1000)))
    nonce = str(uuid.uuid4())
    string_to_sign = f'{token}{t}{nonce}'.encode('utf-8')
    sign = base64.b64encode(
        hmac.new(secret.encode('utf-8'), msg=string_to_sign, digestmod=hashlib.sha256).digest()
    ).decode('utf-8')

    return {
        'Authorization': token,
        't': t,
        'sign': sign,
        'nonce': nonce,
        'Content-Type': 'application/json; charset=utf8'
    }

def send_command(device_id: str, command: str, parameter: str = "default", command_type: str = "command"):
    config = load_config()
    token = config['switchbot']['token']
    secret = config['switchbot']['secret']

    url = f"https://api.switch-bot.com/v1.1/devices/{device_id}/commands"
    headers = generate_headers(token, secret)
    payload = {
        "command": command,
        "parameter": parameter,
        "commandType": command_type
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            print(f"[SwitchBot API] Sent to {device_id} ({command}:{parameter}) -> Response: {res_data}")
            return res_data
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        print(f"[SwitchBot API Error] HTTP {e.code}: {err_body}")
        return {"statusCode": e.code, "message": err_body}
    except Exception as e:
        print(f"[SwitchBot API Error] {e}")
        return {"statusCode": 500, "message": str(e)}

# === エアコン制御 ===
def control_ac(mode: str, temp: int = 26, fan_mode: str = "auto"):
    """
    mode: 'off', 'cool', 'dry', 'heat', 'auto', 'fan_only'
    temp: 16〜30 (通常22〜28)
    fan_mode: 'auto', 'low', 'medium', 'high'
    """
    config = load_config()
    device_id = config['switchbot']['devices'].get('ac')
    if not device_id:
        raise ValueError("AC device ID not found in config.json")

    if mode == 'off':
        return send_command(device_id, "turnOff", "default", "command")

    mode_map = {
        "auto": 1,
        "cool": 2,
        "dry": 3,
        "fan_only": 4,
        "heat": 5
    }
    fan_map = {
        "auto": 1,
        "low": 2,
        "medium": 3,
        "high": 4
    }

    mode_num = mode_map.get(mode, 2)
    fan_num = fan_map.get(fan_mode, 1)
    param = f"{temp},{mode_num},{fan_num},on"

    return send_command(device_id, "setAll", param, "command")

# === ライト制御 ===
def control_light(action: str):
    """
    action: 'on', 'off', 'turnOn', 'turnOff', 'brightnessUp', 'brightnessDown', 'plus', 'minus', 'full', 'night'
    """
    config = load_config()
    device_id = config['switchbot']['devices'].get('light')
    if not device_id:
        raise ValueError("Light device ID not found in config.json")

    # 常夜灯 (SwitchBotアプリ登録のカスタム学習ボタン「常夜灯」)
    if action in ('night', 'nightLight', '常夜灯'):
        return send_command(device_id, "常夜灯", "default", "customize")

    # 全灯 / 点灯 (標準コマンド turnOn)
    if action in ('on', 'turnOn', 'full', 'all'):
        return send_command(device_id, "turnOn", "default", "command")

    # 消灯 (標準コマンド turnOff)
    if action in ('off', 'turnOff'):
        return send_command(device_id, "turnOff", "default", "command")

    # 明るさ調整
    if action in ('brightnessUp', 'plus'):
        return send_command(device_id, "brightnessUp", "default", "command")
    if action in ('brightnessDown', 'minus'):
        return send_command(device_id, "brightnessDown", "default", "command")

    return send_command(device_id, "turnOn", "default", "command")

# === ヒーター制御 ===
def control_heater(action: str):
    """
    action: 'turnOn', 'turnOff', 'toggle', 'eco', 'power', 'plus', 'minus', 'mode'
    """
    config = load_config()
    device_id = config['switchbot']['devices'].get('heater')
    if not device_id:
        raise ValueError("Heater device ID not found in config.json")

    # カスタム学習ボタン (エコ, パワー, プラス, マイナス, モード)
    if action in ('eco', 'エコ'):
        return send_command(device_id, "エコ", "default", "customize")
    if action in ('power', 'パワー'):
        return send_command(device_id, "パワー", "default", "customize")
    if action in ('plus', 'プラス', 'tempUp'):
        return send_command(device_id, "プラス", "default", "customize")
    if action in ('minus', 'マイナス', 'tempDown'):
        return send_command(device_id, "マイナス", "default", "customize")
    if action in ('mode', 'モード'):
        return send_command(device_id, "モード", "default", "customize")

    # 運転ボタン (電源オン/オフ・トグル)
    if action in ('on', 'turnOn'):
        return send_command(device_id, "turnOn", "default", "command")
    if action in ('off', 'turnOff'):
        return send_command(device_id, "turnOff", "default", "command")
    if action == 'toggle':
        return send_command(device_id, "turnOn", "default", "command")

    return send_command(device_id, "turnOn", "default", "command")

if __name__ == '__main__':
    print("Testing AC, Light, and Heater control...")
    cfg = load_config()
    print("Devices in config:", cfg.get('switchbot', {}).get('devices'))
