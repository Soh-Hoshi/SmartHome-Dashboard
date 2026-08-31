#!/usr/bin/env python3
"""
Weather & Solar Service for Kawasaki Nakahara Kizuki
Coordinates: 35.5647 N, 139.6544 E (Kizuki, Nakahara-ku, Kawasaki)
Uses Open-Meteo API (Free, No API key, High Precision JMA/GSM model)
Includes local in-memory & file cache to ensure 0-millisecond instant responses.
"""

import time
import json
import os
import urllib.request

DIRECTORY = os.path.dirname(os.path.realpath(__file__))
CACHE_FILE = os.path.join(DIRECTORY, 'weather_cache.json')
LATITUDE = 35.5647
LONGITUDE = 139.6544
LOCATION_NAME = "川崎市中原区木月"

WMO_WEATHER_MAP = {
    0: "快晴",
    1: "晴れ",
    2: "一部曇り",
    3: "曇り",
    45: "霧",
    48: "霧氷",
    51: "霧雨",
    53: "小雨",
    55: "強い霧雨",
    61: "弱い雨",
    63: "雨",
    65: "激しい雨",
    71: "小雪",
    73: "雪",
    75: "大雪",
    80: "にわか雨",
    81: "強いにわか雨",
    82: "激しいにわか雨",
    95: "雷雨",
    96: "雹を伴う雷雨"
}

_memory_cache = {
    "timestamp": 0,
    "data": None
}

def get_weather_data(force_refresh=False):
    """
    川崎市中原区木月のリアルタイム気象データ（外気温・湿度・天気・昼夜・日の出・日の入り）を取得。
    キャッシュ有効期限: 10分
    """
    global _memory_cache
    now = time.time()

    # 1. メモリキャッシュ (10分以内)
    if not force_refresh and _memory_cache["data"] and (now - _memory_cache["timestamp"] < 600):
        return _memory_cache["data"]

    # 2. ディスクキャッシュ (起動時など)
    if not force_refresh and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                disk_data = json.load(f)
            if now - disk_data.get('cached_at', 0) < 600:
                _memory_cache["timestamp"] = disk_data['cached_at']
                _memory_cache["data"] = disk_data['data']
                return disk_data['data']
        except Exception:
            pass

    # 3. Open-Meteo API から最新データをフェッチ
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LATITUDE}&longitude={LONGITUDE}"
        f"&current=temperature_2m,relative_humidity_2m,weather_code,is_day"
        f"&daily=sunrise,sunset"
        f"&timezone=Asia%2FTokyo"
    )

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'SmartHomeDashboard/1.0'})
        with urllib.request.urlopen(req, timeout=5) as res:
            raw = json.loads(res.read().decode('utf-8'))

        current = raw.get('current', {})
        daily = raw.get('daily', {})

        temp = round(current.get('temperature_2m', 22.0), 1)
        humidity = current.get('relative_humidity_2m', 50)
        is_day = bool(current.get('is_day', 1))
        wcode = current.get('weather_code', 0)
        weather_desc = WMO_WEATHER_MAP.get(wcode, "晴れ")

        sunrise_list = daily.get('sunrise', [])
        sunset_list = daily.get('sunset', [])

        sunrise_str = sunrise_list[0].split('T')[1] if sunrise_list else "05:30"
        sunset_str = sunset_list[0].split('T')[1] if sunset_list else "18:00"

        formatted = {
            "location": LOCATION_NAME,
            "temp": temp,
            "humidity": humidity,
            "is_day": is_day,
            "weather": weather_desc,
            "weather_code": wcode,
            "sunrise": sunrise_str,
            "sunset": sunset_str,
            "updated_at": current.get('time', '')
        }

        _memory_cache["timestamp"] = now
        _memory_cache["data"] = formatted

        # キャッシュファイル保存
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump({"cached_at": now, "data": formatted}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return formatted

    except Exception as e:
        print(f"[Weather API Notice] {e}")
        # フォールバック（既存のメモリキャッシュまたはデフォルト値）
        if _memory_cache["data"]:
            return _memory_cache["data"]
        return {
            "location": LOCATION_NAME,
            "temp": 24.0,
            "humidity": 60,
            "is_day": True,
            "weather": "晴れ",
            "weather_code": 0,
            "sunrise": "05:15",
            "sunset": "18:10",
            "updated_at": ""
        }

if __name__ == '__main__':
    data = get_weather_data(force_refresh=True)
    print("=== 川崎市中原区木月 気象データ ===")
    print(f"場所: {data['location']}")
    print(f"外気温: {data['temp']}℃")
    print(f"湿度: {data['humidity']}%")
    print(f"天気: {data['weather']}")
    print(f"昼夜: {'昼（日照中）' if data['is_day'] else '夜（日没後）'}")
    print(f"日の出: {data['sunrise']}")
    print(f"日の入り: {data['sunset']}")
