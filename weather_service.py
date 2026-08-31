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
import datetime
import urllib.request

DIRECTORY = os.path.dirname(os.path.realpath(__file__))
CACHE_FILE = os.path.join(DIRECTORY, 'weather_cache.json')
LATITUDE = 35.5647
LONGITUDE = 139.6544
LOCATION_NAME = "川崎市中原区木月"

WMO_WEATHER_MAP = {
    0: ("快晴", "wb_sunny", "clear_night"),
    1: ("晴れ", "wb_sunny", "clear_night"),
    2: ("一部曇り", "partly_cloudy_day", "partly_cloudy_night"),
    3: ("曇り", "cloud", "cloud"),
    45: ("霧", "foggy", "foggy"),
    48: ("霧氷", "foggy", "foggy"),
    51: ("霧雨", "grain", "grain"),
    53: ("小雨", "rainy", "rainy"),
    55: ("強い霧雨", "rainy", "rainy"),
    61: ("弱い雨", "rainy", "rainy"),
    63: ("雨", "rainy", "rainy"),
    65: ("激しい雨", "thunderstorm", "thunderstorm"),
    71: ("小雪", "weather_snowy", "weather_snowy"),
    73: ("雪", "weather_snowy", "weather_snowy"),
    75: ("大雪", "weather_snowy", "weather_snowy"),
    80: ("にわか雨", "rainy", "rainy"),
    81: ("強いにわか雨", "rainy", "rainy"),
    82: ("激しいにわか雨", "thunderstorm", "thunderstorm"),
    95: ("雷雨", "thunderstorm", "thunderstorm"),
    96: ("雹を伴う雷雨", "thunderstorm", "thunderstorm")
}

_memory_cache = {
    "timestamp": 0,
    "data": None
}

def get_weather_data(force_refresh=False):
    """
    川崎市中原区木月のリアルタイム気象データおよび1日の時間別予報を取得。
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
        f"&current=temperature_2m,relative_humidity_2m,weather_code,is_day,apparent_temperature,wind_speed_10m"
        f"&hourly=temperature_2m,weather_code,precipitation_probability"
        f"&daily=temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_sum"
        f"&timezone=Asia%2FTokyo"
        f"&forecast_days=2"
    )

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'SmartHomeDashboard/1.0'})
        with urllib.request.urlopen(req, timeout=5) as res:
            raw = json.loads(res.read().decode('utf-8'))

        current = raw.get('current', {})
        daily = raw.get('daily', {})
        hourly = raw.get('hourly', {})

        temp = round(current.get('temperature_2m', 22.0), 1)
        feels_like = round(current.get('apparent_temperature', temp), 1)
        humidity = current.get('relative_humidity_2m', 50)
        wind_speed = round(current.get('wind_speed_10m', 0.0), 1)
        is_day = bool(current.get('is_day', 1))
        wcode = current.get('weather_code', 0)

        weather_info = WMO_WEATHER_MAP.get(wcode, ("晴れ", "wb_sunny", "clear_night"))
        weather_desc = weather_info[0]
        weather_icon = weather_info[1] if is_day else weather_info[2]

        # 日別データ (今日)
        sunrise_list = daily.get('sunrise', [])
        sunset_list = daily.get('sunset', [])
        temp_max_list = daily.get('temperature_2m_max', [])
        temp_min_list = daily.get('temperature_2m_min', [])

        sunrise_str = sunrise_list[0].split('T')[1] if sunrise_list else "05:30"
        sunset_str = sunset_list[0].split('T')[1] if sunset_list else "18:00"
        temp_max = round(temp_max_list[0], 1) if temp_max_list else temp
        temp_min = round(temp_min_list[0], 1) if temp_min_list else temp

        # 時間帯別予報 (現在時刻から24時間分)
        h_times = hourly.get('time', [])
        h_temps = hourly.get('temperature_2m', [])
        h_wcodes = hourly.get('weather_code', [])
        h_pops = hourly.get('precipitation_probability', [])

        current_iso_hour = datetime.datetime.now().strftime('%Y-%m-%dT%H:00')
        start_idx = 0
        for i, t in enumerate(h_times):
            if t >= current_iso_hour:
                start_idx = i
                break

        hourly_forecast = []
        for i in range(start_idx, min(start_idx + 12, len(h_times))):
            t_str = h_times[i].split('T')[1]  # "14:00"
            h_code = h_wcodes[i] if i < len(h_wcodes) else 0
            h_info = WMO_WEATHER_MAP.get(h_code, ("晴れ", "wb_sunny", "clear_night"))
            h_hour = int(t_str.split(':')[0])
            h_is_day = (5 <= h_hour < 18)
            h_icon = h_info[1] if h_is_day else h_info[2]

            hourly_forecast.append({
                "time": t_str,
                "temp": round(h_temps[i], 1) if i < len(h_temps) else 20.0,
                "weather": h_info[0],
                "icon": h_icon,
                "pop": h_pops[i] if i < len(h_pops) else 0
            })

        formatted = {
            "location": LOCATION_NAME,
            "temp": temp,
            "feels_like": feels_like,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "is_day": is_day,
            "weather": weather_desc,
            "weather_icon": weather_icon,
            "weather_code": wcode,
            "temp_max": temp_max,
            "temp_min": temp_min,
            "sunrise": sunrise_str,
            "sunset": sunset_str,
            "hourly": hourly_forecast,
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
        if _memory_cache["data"]:
            return _memory_cache["data"]
        return {
            "location": LOCATION_NAME,
            "temp": 24.0,
            "feels_like": 24.5,
            "humidity": 60,
            "wind_speed": 3.0,
            "is_day": True,
            "weather": "晴れ",
            "weather_icon": "wb_sunny",
            "weather_code": 0,
            "temp_max": 28.0,
            "temp_min": 20.0,
            "sunrise": "05:15",
            "sunset": "18:10",
            "hourly": [],
            "updated_at": ""
        }

if __name__ == '__main__':
    data = get_weather_data(force_refresh=True)
    print("=== 川崎市中原区木月 気象データ ===")
    print(f"場所: {data['location']}")
    print(f"外気温: {data['temp']}℃ (体感: {data['feels_like']}℃)")
    print(f"最高/最低: {data['temp_max']}℃ / {data['temp_min']}℃")
    print(f"天気: {data['weather']} (アイコン: {data['weather_icon']})")
    print(f"湿度: {data['humidity']}% | 風速: {data['wind_speed']} m/s")
    print(f"日の出/日の入り: {data['sunrise']} / {data['sunset']}")
    print(f"時間帯別予報 (件数: {len(data['hourly'])}):")
    for h in data['hourly'][:5]:
        print(f"  {h['time']}: {h['temp']}℃ {h['weather']} (降水確率: {h['pop']}%)")
