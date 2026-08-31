#!/usr/bin/env python3
"""
SmartHome Natural Language Assistant Engine (Nova)
Hybrid Engine: Ultra-fast rule-based parser (0.001s) + Local LLM (Qwen 2.5 via Ollama) fallback
100% Private, Local, Free & Standardized Responses.
"""

import re
import os
import json
import unicodedata
import urllib.request
import urllib.error

DIRECTORY = os.path.dirname(os.path.realpath(__file__))
STATE_FILE = os.path.join(DIRECTORY, 'state.json')
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

def format_standard_message(device, action, params=None):
    """すべての返答メッセージを画一化・統一するフォーマッター (絵文字なし)"""
    params = params or {}
    if device == 'light':
        if action in ('on', 'turnOn'): return "ライトを点灯しました。"
        if action in ('off', 'turnOff'): return "ライトを消灯しました。"
        if action == 'full': return "ライトを全灯（100%）にしました。"
        if action == 'night': return "ライトを常夜灯にしました。"
        if action == 'toggle': return "ライトのオン/オフを切り替えました。"
        return "ライトを設定しました。"
    
    elif device == 'ac':
        mode = params.get('mode', 'cool')
        temp = params.get('temp', 26)
        if mode == 'off': return "エアコンをオフにしました。"
        mode_label = '除湿' if mode == 'dry' else '冷房'
        return f"エアコンを{mode_label}{temp}℃に設定しました。"
    
    elif device == 'heater':
        if action in ('off', 'turnOff'): return "ヒーターをオフにしました。"
        if action == 'eco': return "ヒーターのエコモードを設定しました。"
        temp = params.get('temp', 22)
        return f"ヒーターを暖房{temp}℃に設定しました。"
    
    elif device == 'cleaner':
        if action in ('start', 'run', 'clean', 'play'): return "クリーナーのお掃除を開始しました。"
        if action in ('pause', 'stop'): return "クリーナーを一時停止しました。"
        if action in ('home', 'dock', 'return'): return "クリーナーを充電ドックへ戻します。"
        if action in ('find', 'find_me', 'beep'): return "クリーナーの位置探索アラームを鳴らします。"
        return "クリーナーを設定しました。"
    
    elif device == 'scene':
        if action == 'all_off': return "おやすみなさい。ライトと空調をすべてオフにしました。"
        if action == 'welcome': return "おかえりなさい。ライトを点灯し、エアコンを冷房26℃で起動しました。"
        if action == 'morning': return "おはようございます。ライトを点灯しました。"
    
    return "操作を完了しました。"

def query_local_llm(prompt_text):
    """ローカルOllama (Qwen 2.5 1.5B) で複雑な自然言語コマンドをパース"""
    system_prompt = """あなたはスマートホームAI「Nova」です。ユーザーの要望が家電操作に該当する場合のみ以下のJSON形式を出力してください。
操作可能デバイス:
- light: {"device": "light", "action": "on"|"off"|"full"|"night"}
- ac: {"device": "ac", "mode": "cool"|"dry"|"off", "temp": 22..28, "fan": "auto"}
- heater: {"device": "heater", "action": "heat"|"off"|"eco", "temp": 22..28}
- cleaner: {"device": "cleaner", "action": "start"|"pause"|"home"|"find"}

重要: 雑談や家電操作と無関係な言葉の場合は {"device": "none"} を出力してください。
出力形式(JSONのみ):
{"device": "...", "action": "...", "temp": 24, "mode": "cool"}"""

    req_data = {
        'model': 'qwen2.5:1.5b',
        'prompt': f"{system_prompt}\nユーザー: {prompt_text}\n出力:",
        'stream': False,
        'format': 'json',
        'options': {'temperature': 0.1, 'num_predict': 40}
    }
    try:
        req = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps(req_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=4) as res:
            resp_data = json.loads(res.read().decode('utf-8'))
            raw_text = resp_data.get('response', '{}')
            parsed = json.loads(raw_text)
            return parsed
    except Exception as e:
        print(f"[Local LLM Fallback Notice] {e}")
        return None

def parse_and_execute(prompt: str, send_api_fn=None):
    """
    自然言語プロンプトを解釈し、対応する家電アクションを実行して画一化された応答テキストを返す。
    誤操作防止ガード付き。
    """
    if not prompt or not prompt.strip():
        return {
            "success": False,
            "message": "コマンドを入力してください。",
            "action": None
        }

    # 全角英数→半角正規化、小文字化、前後の空白除去
    text = unicodedata.normalize('NFKC', prompt).strip().lower()

    # -------------------------------------------------------------
    # 0. 呼びかけ・挨拶・軽い雑談ガード（家電を一切誤作動させない）
    # -------------------------------------------------------------
    # 呼びかけ単体
    if text in ('nova', 'ノヴァ', 'ノバ', 'のゔぁ', 'のば', 'nova!', 'nova?', 'ノヴァ！', 'ノヴァ？', 'ノバ！', 'ノバ？'):
        return {"success": True, "message": "はい、Novaです。何か操作しますか？", "action": "wake"}

    # 挨拶・軽い雑談
    if text in ('やあ', 'やあやあ', 'こんにちは', 'こんばんは', 'どうも', 'ヘイ', 'へい', 'おーい', 'おい', 'hi', 'hello', 'hey'):
        return {"success": True, "message": "こんにちは！何か操作しますか？", "action": "greeting"}

    if text in ('ありがとう', 'ありがと', 'サンキュー', 'さんきゅー', 'thanks', 'thank you', 'お疲れ', 'おつかれ', '助かった'):
        return {"success": True, "message": "どういたしまして！", "action": "thanks"}

    if text in ('テスト', 'test', 'てすと', 'チェック', 'あ', 'ああ', 'うん'):
        return {"success": True, "message": "はい、待機しています。", "action": "test"}

    # 先頭の「Nova、」「ノヴァ、」「ノバ 」などの呼びかけを除去
    clean_text = re.sub(r'^(nova|ノヴァ|ノバ|のゔぁ|のば)[、,\s]*', '', text).strip()
    if not clean_text:
        return {"success": True, "message": "はい、Novaです。何か操作しますか？", "action": "wake"}

    text = clean_text

    # -------------------------------------------------------------
    # 第1段階：ミリ秒レベルの超高速ルールベース（日常の98%を即答）
    # -------------------------------------------------------------

    # 1. 状態確認 (Status)
    if any(k in text for k in ['状態', 'ステータス', 'どうなってる', '今の設定', '確認', 'status', 'じょうたい']):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    st = json.load(f)
                light_st = '点灯中' if st.get('lightOn') else '消灯'
                if st.get('lightFull'): light_st = '全灯'
                elif st.get('lightNight'): light_st = '常夜灯'
                
                ac_st = f"冷房 {st.get('acTemp', 26)}℃" if st.get('acMode') == 'cool' else ('除湿' if st.get('acMode') == 'dry' else '停止中')
                heater_st = f"暖房 {st.get('heaterTemp', 22)}℃" if st.get('heaterMode') == 'heat' else '停止中'
                cleaner_st = st.get('cleanerStatus', 'standby')
                cleaner_map = {'running': '掃除中', 'charging': '充電中', 'recharge': '充電に戻り中', 'standby': '待機中', 'completed': '掃除完了'}
                cleaner_desc = cleaner_map.get(cleaner_st, cleaner_st)

                msg = f"現在の状態：ライトは{light_st}、エアコンは{ac_st}、ヒーターは{heater_st}、クリーナーは{cleaner_desc}です。"
                return {"success": True, "message": msg, "action": "status"}
            except Exception:
                pass
        return {"success": True, "message": "機器の状態を確認しました。", "action": "status"}

    # 2. クリーナー / 掃除 (Cleaner)
    if any(k in text for k in ['掃除', 'そうじ', 'クリーナー', 'くりーなー', '掃除機', 'そうじき', 'ルンバ', 'るんば', 'eufy', 'vacuum', 'cleaner']):
        if any(k in text for k in ['帰って', 'かえって', 'おうち', '戻って', 'もどって', '充電', 'じゅうでん', 'ホーム', 'ほーむ', 'ドック', 'どっく', 'dock', 'home', 'やめて', '終了', 'しゅうりょう', '終わり', 'おわり']):
            if send_api_fn: send_api_fn('/api/cleaner', {'action': 'home'})
            return {"success": True, "message": format_standard_message('cleaner', 'home'), "action": "cleaner_home"}
        elif any(k in text for k in ['一時停止', 'いちじていし', '止めて', 'とめて', 'ストップ', 'すとっぷ', 'pause', 'stop', '待って', 'まって']):
            if send_api_fn: send_api_fn('/api/cleaner', {'action': 'pause'})
            return {"success": True, "message": format_standard_message('cleaner', 'pause'), "action": "cleaner_pause"}
        elif any(k in text for k in ['探して', 'さがして', 'どこ', '鳴らして', 'ならして', 'find', 'beep']):
            if send_api_fn: send_api_fn('/api/cleaner', {'action': 'find'})
            return {"success": True, "message": format_standard_message('cleaner', 'find'), "action": "cleaner_find"}
        else:
            if send_api_fn: send_api_fn('/api/cleaner', {'action': 'start'})
            return {"success": True, "message": format_standard_message('cleaner', 'start'), "action": "cleaner_start"}

    # 3. ライト / 照明 (Light)
    if any(k in text for k in ['ライト', 'らいと', '電気', 'でんき', '照明', 'しょうめい', 'あかり', '明かり', 'light']):
        if any(k in text for k in ['消して', 'けして', 'オフ', 'おふ', '消灯', 'しょうとう', '暗く', 'くらく', 'off', '切って', 'きって', '消す', 'けす', '落として', 'おとして']):
            if send_api_fn: send_api_fn('/api/light', {'action': 'off'})
            return {"success": True, "message": format_standard_message('light', 'off'), "action": "light_off"}
        elif any(k in text for k in ['全灯', 'ぜんとう', 'マックス', '最大', 'さいだい', '明るく', 'あかるく', 'full', '100%']):
            if send_api_fn: send_api_fn('/api/light', {'action': 'full'})
            return {"success": True, "message": format_standard_message('light', 'full'), "action": "light_full"}
        elif any(k in text for k in ['常夜灯', 'じょうやとう', '夜間', 'やかん', '豆電球', 'まめでんきゅう', 'ナイト', 'ないと', 'night', '暗め', 'くらめ']):
            if send_api_fn: send_api_fn('/api/light', {'action': 'night'})
            return {"success": True, "message": format_standard_message('light', 'night'), "action": "light_night"}
        elif any(k in text for k in ['つけて', '点けて', 'オン', 'おん', '点灯', 'てんとう', 'on', 'つける', '明かり', '点火']):
            if send_api_fn: send_api_fn('/api/light', {'action': 'on'})
            return {"success": True, "message": format_standard_message('light', 'on'), "action": "light_on"}
        elif any(k in text for k in ['トグル', '切り替え', 'きりかえ', 'toggle']):
            if send_api_fn: send_api_fn('/api/light', {'action': 'toggle'})
            return {"success": True, "message": format_standard_message('light', 'toggle'), "action": "light_toggle"}

    # 4. エアコン / クーラー / 冷房 / 除湿 (AC)
    if any(k in text for k in ['エアコン', 'えあこん', 'クーラー', 'くーらー', '冷房', 'れいぼう', '除湿', 'じょしつ', 'ドライ', 'どらい', 'ac', 'aircon']):
        if any(k in text for k in ['消して', 'けして', 'オフ', 'おふ', '止めて', 'とめて', '切って', 'きって', 'off', 'stop', '消す', 'けす']):
            if send_api_fn: send_api_fn('/api/ac', {'mode': 'off'})
            return {"success": True, "message": format_standard_message('ac', 'off', {'mode': 'off'}), "action": "ac_off"}

        temp_match = re.search(r'(\d{2})\s*(度|℃|c)?', text)
        temp = int(temp_match.group(1)) if temp_match else 26
        temp = max(22, min(28, temp))
        mode = 'dry' if any(k in text for k in ['除湿', 'じょしつ', 'ドライ', 'どらい', 'dry']) else 'cool'
        if send_api_fn: send_api_fn('/api/ac', {'mode': mode, 'temp': temp, 'fan_mode': 'auto'})
        return {"success": True, "message": format_standard_message('ac', 'on', {'mode': mode, 'temp': temp}), "action": f"ac_{mode}_{temp}"}

    # 温度のみの指定（「24度」「24度にして」「25℃設定」など）
    if re.search(r'^\s*(\d{2})\s*(度|℃|c)?(にして|に設定|にしてよ|設定|)?\s*$', text):
        temp = int(re.search(r'(\d{2})', text).group(1))
        temp = max(22, min(28, temp))
        if send_api_fn: send_api_fn('/api/ac', {'mode': 'cool', 'temp': temp, 'fan_mode': 'auto'})
        return {"success": True, "message": format_standard_message('ac', 'on', {'mode': 'cool', 'temp': temp}), "action": f"ac_cool_{temp}"}

    # 5. ヒーター / 暖房 (Heater)
    if any(k in text for k in ['ヒーター', 'ひーたー', '暖房', 'だんぼう', 'ストーブ', 'すとーぶ', 'heater', 'heat']):
        if any(k in text for k in ['消して', 'けして', 'オフ', 'おふ', '止めて', 'とめて', '切って', 'きって', 'off', 'stop']):
            if send_api_fn: send_api_fn('/api/heater', {'action': 'off'})
            return {"success": True, "message": format_standard_message('heater', 'off'), "action": "heater_off"}
        elif any(k in text for k in ['エコ', 'えこ', 'eco']):
            if send_api_fn: send_api_fn('/api/heater', {'action': 'eco'})
            return {"success": True, "message": format_standard_message('heater', 'eco'), "action": "heater_eco"}
        else:
            temp_match = re.search(r'(\d{2})\s*(度|℃|c)?', text)
            temp = int(temp_match.group(1)) if temp_match else 22
            temp = max(22, min(28, temp))
            if send_api_fn: send_api_fn('/api/heater', {'action': 'heat', 'temp': temp})
            return {"success": True, "message": format_standard_message('heater', 'heat', {'temp': temp}), "action": f"heater_heat_{temp}"}

    # 6. 一括操作 (シーン / 全消し)
    if any(k in text for k in ['おやすみ', '寝る', 'ねる', '就寝', '外出', 'がいしゅつ', 'いってきます', '全部消して', '全消し', 'ぜんぶけして', '消灯して']):
        if send_api_fn:
            send_api_fn('/api/light', {'action': 'off'})
            send_api_fn('/api/ac', {'mode': 'off'})
            send_api_fn('/api/heater', {'action': 'off'})
        return {"success": True, "message": format_standard_message('scene', 'all_off'), "action": "all_off"}

    if any(k in text for k in ['ただいま', '帰宅', 'きたく', 'ついた', '着いた']):
        if send_api_fn:
            send_api_fn('/api/light', {'action': 'on'})
            send_api_fn('/api/ac', {'mode': 'cool', 'temp': 26, 'fan_mode': 'auto'})
        return {"success": True, "message": format_standard_message('scene', 'welcome'), "action": "welcome"}

    if any(k in text for k in ['おはよう', '起きた', 'おきた']):
        if send_api_fn:
            send_api_fn('/api/light', {'action': 'on'})
        return {"success": True, "message": format_standard_message('scene', 'morning'), "action": "light_on"}

    # -------------------------------------------------------------
    # 第2段階：ローカルAI（Qwen 2.5 1.5B）による高度推論フォールバック
    # -------------------------------------------------------------
    llm_res = query_local_llm(prompt)
    if llm_res and isinstance(llm_res, dict):
        device = llm_res.get('device')

        if device == 'light':
            act = llm_res.get('action', 'on')
            if act in ('on', 'off', 'full', 'night', 'toggle'):
                if send_api_fn: send_api_fn('/api/light', {'action': act})
                return {"success": True, "message": format_standard_message('light', act), "action": f"light_{act}"}

        elif device == 'ac':
            mode = llm_res.get('mode', 'cool')
            temp = int(llm_res.get('temp', 26))
            fan = llm_res.get('fan', 'auto')
            if send_api_fn: send_api_fn('/api/ac', {'mode': mode, 'temp': temp, 'fan_mode': fan})
            return {"success": True, "message": format_standard_message('ac', 'on' if mode != 'off' else 'off', {'mode': mode, 'temp': temp}), "action": f"ac_{mode}_{temp}"}

        elif device == 'heater':
            act = llm_res.get('action', 'heat')
            temp = int(llm_res.get('temp', 22))
            if send_api_fn: send_api_fn('/api/heater', {'action': act, 'temp': temp})
            return {"success": True, "message": format_standard_message('heater', act, {'temp': temp}), "action": f"heater_{act}"}

        elif device == 'cleaner':
            act = llm_res.get('action', 'start')
            if send_api_fn: send_api_fn('/api/cleaner', {'action': act})
            return {"success": True, "message": format_standard_message('cleaner', act), "action": f"cleaner_{act}"}

    # -------------------------------------------------------------
    # 第3段階：解釈不能の場合（家電を動かさず安全に応答）
    # -------------------------------------------------------------
    return {
        "success": False,
        "message": f"「{prompt}」に対応する操作が見つかりませんでした。",
        "action": None
    }

if __name__ == '__main__':
    import sys
    test_queries = [
        "やあ",
        "ありがとう",
        "テスト",
        "Nova",
        "Nova、電気消して",
        "掃除開始",
        "今日の天気は？"
    ]
    for q in test_queries:
        res = parse_and_execute(q, lambda ep, data: None)
        print(f"[{q}] -> {res.get('message')}")
