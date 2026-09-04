#!/usr/bin/env python3
"""
Automation Service for SmartHome Dashboard
Handles scheduled triggers such as weekday morning light-on (06:30 JST, excluding weekends & JP holidays).
"""

import time
import datetime
import threading
import json
import os
import urllib.request

CONFIG_PATH = "/home/soh/dashboard/automations_config.json"

# 日本の祝日計算 (2024年〜2030年対応 / 春分・秋分および振替休日対応)
def is_japanese_holiday(dt: datetime.date) -> bool:
    """日本の祝日（振替休日含む）かどうかを判定"""
    year = dt.year
    month = dt.month
    day = dt.day
    weekday = dt.weekday() # 0: 月, 6: 日

    # 1. 固定祝日
    fixed_holidays = {
        (1, 1): "元日",
        (2, 11): "建国記念の日",
        (2, 23): "天皇誕生日",
        (4, 29): "昭和の日",
        (5, 3): "憲法記念日",
        (5, 4): "みどりの日",
        (5, 5): "こどもの日",
        (8, 11): "山の日",
        (11, 3): "文化の日",
        (11, 23): "勤労感謝の日",
    }

    # 2. ハッピーマンデー (第N月曜日)
    # 成人の日: 1月第2月曜
    # 海の日: 7月第3月曜
    # 敬老の日: 9月第3月曜
    # スポーツの日: 10月第2月曜
    def is_nth_monday(target_month, n):
        if month != target_month or weekday != 0:
            return False
        return (day - 1) // 7 + 1 == n

    # 3. 春分の日 / 秋分の日 (簡易天文学計算)
    vernal_equinox = int(20.8431 + 0.242194 * (year - 1980) - int((year - 1980) / 4))
    autumn_equinox = int(23.2488 + 0.242194 * (year - 1980) - int((year - 1980) / 4))

    is_holiday = False
    if (month, day) in fixed_holidays:
        is_holiday = True
    elif is_nth_monday(1, 2):  # 成人の日
        is_holiday = True
    elif is_nth_monday(7, 3):  # 海の日
        is_holiday = True
    elif is_nth_monday(9, 3):  # 敬老の日
        is_holiday = True
    elif is_nth_monday(10, 2): # スポーツの日
        is_holiday = True
    elif month == 3 and day == vernal_equinox:
        is_holiday = True
    elif month == 9 and day == autumn_equinox:
        is_holiday = True
    elif month == 5 and day == 6 and weekday in (1, 2, 3): # GW振替
        is_holiday = True

    # 振替休日判定: 祝日が日曜日の場合、翌月曜日が振替休日
    if not is_holiday and weekday == 0:
        yesterday = dt - datetime.timedelta(days=1)
        if is_japanese_holiday(yesterday):
            return True

    return is_holiday

def is_japanese_business_day(dt: datetime.date) -> bool:
    """土日および祝日を除く平日かどうかを判定"""
    if dt.weekday() >= 5: # 土曜日(5), 日曜日(6)
        return False
    if is_japanese_holiday(dt):
        return False
    return True

DEFAULT_AUTOMATIONS = [
    {
        "id": "weekday_morning_light",
        "name": "平日 6:30",
        "category": "デイリー",
        "enabled": False,
        "trigger": {
            "type": "time",
            "time": "06:30",
            "condition": "日本の平日（土日祝除く）"
        },
        "flow": [
            {
                "target": "リビング",
                "action": "オン",
                "condition": None,
                "icon": "lightbulb",
                "iconColor": "text-amber-400",
                "bgColor": "bg-amber-500/10"
            }
        ],
        "command": "smarthome light on"
    },
    {
        "id": "weekday_morning_cleaner",
        "name": "平日 9:00",
        "category": "デイリー",
        "enabled": True,
        "trigger": {
            "type": "time",
            "time": "09:00",
            "condition": "日本の平日（土日祝除く）"
        },
        "flow": [
            {
                "target": "クリーナー",
                "action": "開始",
                "condition": None,
                "icon": "cleaning_services",
                "iconColor": "text-sky-400",
                "bgColor": "bg-sky-500/10"
            }
        ],
        "command": "smarthome cleaner start"
    }
]

_lock = threading.Lock()

def load_automations():
    if not os.path.exists(CONFIG_PATH):
        save_automations(DEFAULT_AUTOMATIONS)
        return DEFAULT_AUTOMATIONS
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_AUTOMATIONS

def save_automations(data):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Automation Save Error] {e}")

def toggle_automation(auto_id):
    with _lock:
        autos = load_automations()
        for a in autos:
            if a["id"] == auto_id:
                a["enabled"] = not a.get("enabled", True)
                save_automations(autos)
                return a
    return None

import state_manager

def trigger_away_check():
    """
    在宅 ➔ 不在 変化時に呼ばれる消し忘れチェック＆プッシュ通知トリガー
    """
    autos = load_automations()
    away_auto = next((a for a in autos if a.get("id") == "away_device_warning"), None)
    if not away_auto or not away_auto.get("enabled", True):
        return

    st = state_manager.load_state()

    active_devices = []
    if st.get('lightOn', False):
        active_devices.append('リビング照明')
    if st.get('acMode', 'off') != 'off':
        mode_str = 'エアコン（冷房）' if st.get('acMode') == 'cool' else ('エアコン（除湿）' if st.get('acMode') == 'dry' else 'エアコン')
        active_devices.append(mode_str)
    if st.get('heaterMode', 'off') != 'off':
        active_devices.append('ヒーター')

    if active_devices:
        devices_str = '・'.join(active_devices)
        print(f"[Automation Alert] Away detected with active devices: {devices_str}")
        try:
            import push_service
            push_service.send_away_device_warning(devices_str)
        except Exception as e:
            print(f"[Push Trigger Error] {e}")
    else:
        print("[Automation Alert] 外出検知: 電気等の稼働機器がないため、消し忘れ通知をスキップしました。")

def execute_automation(auto_id):
    from serve import dispatch_internal_api
    if auto_id == "away_device_warning":
        trigger_away_check()
        return True
    elif auto_id in ("weekday_morning_light", "平日 6:30"):
        dispatch_internal_api('/api/light', {'action': 'on'})
        return True
    elif auto_id in ("weekday_morning_cleaner", "平日 9:00", "weekday_cleaner"):
        dispatch_internal_api('/api/cleaner', {'action': 'start'})
        try:
            import push_service
            push_service.push_notification(
                title="オートメーション実行",
                body="平日 9:00：ロボット掃除機を開始しました。",
                notif_id="weekday_cleaner_alert"
            )
        except Exception as e:
            print(f"[Automation Notification Error] {e}")
        return True
    return False

def _automation_scheduler_worker():
    last_triggered_minute = ""
    while True:
        try:
            now = datetime.datetime.now()
            current_time_str = now.strftime("%H:%M")
            today_date = now.date()

            # 同じ分に多重実行されないように制御
            if current_time_str != last_triggered_minute:
                is_biz_day = is_japanese_business_day(today_date)
                
                autos = load_automations()
                for a in autos:
                    if not a.get("enabled", True):
                        continue
                    
                    trig = a.get("trigger", {})
                    if trig.get("type") == "time":
                        # 06:30 平日トリガー
                        if trig.get("time") == current_time_str:
                            if "日本の平日" in trig.get("condition", ""):
                                if is_biz_day:
                                    print(f"[Automation Triggered] {a['name']} at {current_time_str} on business day {today_date}")
                                    execute_automation(a["id"])
                            else:
                                print(f"[Automation Triggered] {a['name']} at {current_time_str}")
                                execute_automation(a["id"])

                last_triggered_minute = current_time_str
        except Exception as e:
            print(f"[Automation Worker Error] {e}")

        time.sleep(10)

def start_automation_service():
    t = threading.Thread(target=_automation_scheduler_worker, daemon=True, name="AutomationScheduler")
    t.start()

if __name__ == '__main__':
    now = datetime.datetime.now()
    print(f"Current Date: {now.date()} (Weekday: {now.strftime('%A')})")
    print(f"Is Japanese Holiday? {is_japanese_holiday(now.date())}")
    print(f"Is Japanese Business Day? {is_japanese_business_day(now.date())}")
