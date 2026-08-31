#!/usr/bin/env python3
"""
SmartHome Natural Language Assistant Engine
Parses user natural language queries and executes matching smart home actions.
Supports fast pattern matching + LLM fallback.
"""

import re
import os
import json
import urllib.request

DIRECTORY = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILE = os.path.join(DIRECTORY, 'config.json')

def parse_and_execute(prompt: str, send_api_fn=None):
    """
    自然言語プロンプトを解釈し、対応する家電アクションを実行して応答テキストを返す。
    """
    if not prompt or not prompt.strip():
        return {
            "success": False,
            "message": "コマンドを入力してください。",
            "action": None
        }

    text = prompt.strip().lower()

    # -------------------------------------------------------------
    # 1. 状態確認 (Status)
    # -------------------------------------------------------------
    if any(k in text for k in ['状態', 'ステータス', 'どうなってる', '今の設定', '確認', 'status']):
        state_file = os.path.join(DIRECTORY, 'state.json')
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    st = json.load(f)
                light_st = '点灯中' if st.get('lightOn') else '消灯'
                if st.get('lightFull'): light_st = '全灯'
                elif st.get('lightNight'): light_st = '常夜灯'
                
                ac_st = f"冷房 {st.get('acTemp', 26)}℃" if st.get('acMode') == 'cool' else ('除湿' if st.get('acMode') == 'dry' else '停止中')
                heater_st = f"暖房 {st.get('heaterTemp', 22)}℃" if st.get('heaterMode') == 'heat' else '停止中'
                cleaner_st = st.get('cleanerStatus', 'standby')
                cleaner_map = {'running': '掃除中', 'charging': '充電中', 'recharge': '充電に戻り中', 'standby': '待機中', 'completed': '掃除完了'}
                cleaner_desc = cleaner_map.get(cleaner_st, cleaner_st)

                msg = f"現在の状態です：ライトは{light_st}、エアコンは{ac_st}、ヒーターは{heater_st}、掃除機は{cleaner_desc}です。"
                return {"success": True, "message": msg, "action": "status"}
            except Exception:
                pass
        return {"success": True, "message": "機器の状態を確認しました。", "action": "status"}

    # -------------------------------------------------------------
    # 2. ライト (Light)
    # -------------------------------------------------------------
    if any(k in text for k in ['ライト', '電気', '照明', 'あかり', '明かり', 'light']):
        if any(k in text for k in ['消して', 'けして', 'オフ', '消灯', '暗く', 'off', '切って']):
            if send_api_fn: send_api_fn('/api/light', {'action': 'off'})
            return {"success": True, "message": "💡 リビングのライトを消灯しました。", "action": "light_off"}
        elif any(k in text for k in ['全灯', 'マックス', '最大', '明るく', 'full', '100%']):
            if send_api_fn: send_api_fn('/api/light', {'action': 'full'})
            return {"success": True, "message": "💡 ライトを全灯（100%）にしました。", "action": "light_full"}
        elif any(k in text for k in ['常夜灯', '夜間', '豆電球', 'ナイト', 'night']):
            if send_api_fn: send_api_fn('/api/light', {'action': 'night'})
            return {"success": True, "message": "💡 ライトを常夜灯にしました。", "action": "light_night"}
        elif any(k in text for k in ['つけて', '点けて', 'オン', '点灯', 'on']):
            if send_api_fn: send_api_fn('/api/light', {'action': 'on'})
            return {"success": True, "message": "💡 リビングのライトを点灯しました。", "action": "light_on"}
        elif any(k in text for k in ['トグル', '切り替え', 'toggle']):
            if send_api_fn: send_api_fn('/api/light', {'action': 'toggle'})
            return {"success": True, "message": "💡 ライトのオン/オフを切り替えました。", "action": "light_toggle"}

    # -------------------------------------------------------------
    # 3. エアコン / クーラー (AC)
    # -------------------------------------------------------------
    if any(k in text for k in ['エアコン', 'クーラー', '冷房', '除湿', 'ドライ', 'ac', 'aircon']):
        if any(k in text for k in ['消して', 'けして', 'オフ', '止めて', '切って', 'off', 'stop']):
            if send_api_fn: send_api_fn('/api/ac', {'mode': 'off'})
            return {"success": True, "message": "❄️ エアコンをオフにしました。", "action": "ac_off"}

        # 温度抽出 (例: 24度, 26℃, 25)
        temp_match = re.search(r'(\d{2})\s*(度|℃|c)?', text)
        temp = int(temp_match.group(1)) if temp_match else 26
        temp = max(22, min(28, temp))

        mode = 'dry' if any(k in text for k in ['除湿', 'ドライ', 'dry']) else 'cool'
        if send_api_fn: send_api_fn('/api/ac', {'mode': mode, 'temp': temp, 'fan_mode': 'auto'})
        
        mode_label = '除湿' if mode == 'dry' else '冷房'
        return {"success": True, "message": f"❄️ エアコンを{mode_label}{temp}℃に設定しました。", "action": f"ac_{mode}_{temp}"}

    # 温度のみの指定（「24度にして」など）
    if re.search(r'^\s*(\d{2})\s*(度|℃|c)?(にして|に設定|にしてよ|)?\s*$', text):
        temp = int(re.search(r'(\d{2})', text).group(1))
        temp = max(22, min(28, temp))
        if send_api_fn: send_api_fn('/api/ac', {'mode': 'cool', 'temp': temp, 'fan_mode': 'auto'})
        return {"success": True, "message": f"❄️ エアコンを冷房{temp}℃に設定しました。", "action": f"ac_cool_{temp}"}

    # -------------------------------------------------------------
    # 4. ヒーター / 暖房 (Heater)
    # -------------------------------------------------------------
    if any(k in text for k in ['ヒーター', '暖房', 'ストーブ', 'heater', 'heat']):
        if any(k in text for k in ['消して', 'けして', 'オフ', '止めて', '切って', 'off']):
            if send_api_fn: send_api_fn('/api/heater', {'action': 'off'})
            return {"success": True, "message": "🔥 ヒーターをオフにしました。", "action": "heater_off"}
        elif any(k in text for k in ['エコ', 'eco']):
            if send_api_fn: send_api_fn('/api/heater', {'action': 'eco'})
            return {"success": True, "message": "🔥 ヒーターのエコモードを切り替えました。", "action": "heater_eco"}
        else:
            temp_match = re.search(r'(\d{2})\s*(度|℃|c)?', text)
            temp = int(temp_match.group(1)) if temp_match else 22
            temp = max(22, min(28, temp))
            if send_api_fn: send_api_fn('/api/heater', {'action': 'heat', 'temp': temp})
            return {"success": True, "message": f"🔥 ヒーターを暖房{temp}℃で開始しました。", "action": f"heater_heat_{temp}"}

    # -------------------------------------------------------------
    # 5. ロボット掃除機 (Eufy Cleaner / Vacuum)
    # -------------------------------------------------------------
    if any(k in text for k in ['掃除機', 'ルンバ', 'ロボット掃除機', 'クリーナー', 'eufy', 'vacuum', 'cleaner', '掃除']):
        if any(k in text for k in ['帰って', 'おうち', '戻って', '充電', 'ホーム', 'ドック', 'dock', 'home', 'やめて', '終了']):
            if send_api_fn: send_api_fn('/api/cleaner', {'action': 'home'})
            return {"success": True, "message": "🤖 ロボット掃除機を充電ドックへ戻します。", "action": "cleaner_home"}
        elif any(k in text for k in ['一時停止', '止めて', 'ストップ', 'pause', 'stop', '待って']):
            if send_api_fn: send_api_fn('/api/cleaner', {'action': 'pause'})
            return {"success": True, "message": "🤖 ロボット掃除機を一時停止しました。", "action": "cleaner_pause"}
        elif any(k in text for k in ['探して', 'どこ', '鳴らして', 'find', 'beep']):
            if send_api_fn: send_api_fn('/api/cleaner', {'action': 'find'})
            return {"success": True, "message": "🤖 ロボット掃除機の位置探索アラームを鳴らします。", "action": "cleaner_find"}
        elif any(k in text for k in ['して', 'かけて', '開始', 'スタート', 'やって', 'start', 'run', 'お願い']):
            if send_api_fn: send_api_fn('/api/cleaner', {'action': 'start'})
            return {"success": True, "message": "🤖 ロボット掃除機のお掃除を開始しました。", "action": "cleaner_start"}

    # -------------------------------------------------------------
    # 6. 一括操作 (シーン / 全消し)
    # -------------------------------------------------------------
    if any(k in text for k in ['おやすみ', '寝る', '外出', 'いってきます', '全部消して', '全消し']):
        if send_api_fn:
            send_api_fn('/api/light', {'action': 'off'})
            send_api_fn('/api/ac', {'mode': 'off'})
            send_api_fn('/api/heater', {'action': 'off'})
        return {"success": True, "message": "🌙 おやすみなさい。ライトと空調をすべてオフにしました。", "action": "all_off"}

    if any(k in text for k in ['ただいま', '帰宅', 'ついた']):
        if send_api_fn:
            send_api_fn('/api/light', {'action': 'on'})
            send_api_fn('/api/ac', {'mode': 'cool', 'temp': 26, 'fan_mode': 'auto'})
        return {"success": True, "message": "✨ おかえりなさい！ライトを点灯し、エアコンを冷房26℃で起動しました。", "action": "welcome"}

    # -------------------------------------------------------------
    # 7. 解釈不能の場合
    # -------------------------------------------------------------
    return {
        "success": False,
        "message": f"「{prompt}」に対応する操作が見つかりませんでした。「電気消して」「エアコン25度」「掃除機開始」などをお試しください。",
        "action": None
    }

if __name__ == '__main__':
    import sys
    test_query = sys.argv[1] if len(sys.argv) > 1 else "リビングの電気消して"
    res = parse_and_execute(test_query, print)
    print(res)
