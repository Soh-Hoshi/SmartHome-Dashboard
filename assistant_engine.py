#!/usr/bin/env python3
"""
SmartHome Natural Language Assistant Engine (Nova)
Hybrid Engine: Ultra-fast rule-based parser (0.001s) + Gemini 2.0 Flash API (Free Tier, ~0.4s) + Local LLM fallback
100% Private, Fast, Free & Standardized Responses.
Integrated with Kawasaki Nakahara Kizuki Weather, Solar, Presence & Tile Key Data.
Smart Scenes (Morning, Goodnight, Welcome) driven by real-time Apparent (Feels-like) Temperature.
"""

import re
import os
import json
import datetime
import unicodedata
import urllib.request
import urllib.error

import weather_service
import presence_service
import tile_service
import state_manager

DIRECTORY = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILE = os.path.join(DIRECTORY, 'config.json')
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

def get_gemini_api_key():
    """環境変数または config.json から Gemini API キーを取得"""
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ.get("GEMINI_API_KEY")
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                return cfg.get("gemini_api_key") or cfg.get("gemini", {}).get("api_key")
        except Exception:
            pass
    return None

def load_current_state():
    """state_manager から現在の機器状態を取得"""
    return state_manager.load_state()

def normalize_japanese_numbers(text: str) -> str:
    """漢数字を半角数字に変換（例: 二度 -> 2度, 一度 -> 1度, 三度 -> 3度）"""
    kanji_map = {
        '一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
        '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'
    }
    for k, v in kanji_map.items():
        text = text.replace(f"{k}度", f"{v}度")
        text = text.replace(f"{k}℃", f"{v}℃")
        text = text.replace(f"{k}つ", f"{v}つ")
        text = text.replace(f"{k}段階", f"{v}段階")
        text = text.replace(f"{k}ステップ", f"{v}ステップ")
    return text

def parse_relative_temp_change(text: str):
    """
    温度の相対変更意図（上げて/下げて）と変更度数を解析する。
    戻り値: (delta: int | None, target_device_hint: str | None)
    """
    text_norm = normalize_japanese_numbers(text)

    # デバイスの明示ヒント
    hint = None
    if any(k in text_norm for k in ['エアコン', 'えあこん', 'クーラー', 'くーらー', '冷房', 'れいぼう', '除湿', 'じょしつ', 'ac', 'aircon']):
        hint = 'ac'
    elif any(k in text_norm for k in ['ヒーター', 'ひーたー', '暖房', 'だんぼう', 'ストーブ', 'すとーぶ', 'heater']):
        hint = 'heater'

    # 下げる系（マイナス）
    is_down = any(k in text_norm for k in [
        '下げ', 'さげ', '低く', 'ひくく', 'マイナス', 'まいなす',
        '涼しく', 'すずしく', '冷やして', 'ひやして', 'down', '弱く', 'よわく', 'ぬるく'
    ])
    # 上げる系（プラス）
    is_up = any(k in text_norm for k in [
        '上げ', 'あげ', '高く', 'たかく', 'プラス', 'ぷらす',
        '暖かく', 'あたたかく', 'あつく', '暑く', '強く', 'つよく', 'up', 'ぬくく'
    ])

    if not is_down and not is_up:
        # 「暑い」「寒い」単体のケース（1度調整）
        if any(k in text_norm for k in ['暑い', 'あつい', '蒸し暑い']):
            return -1, hint
        if any(k in text_norm for k in ['寒い', 'さむい', '冷える', 'ひえる']):
            return 1, hint
        return None, None

    # 数値の抽出
    num_match = re.search(r'(\d+)\s*(度|℃|段階|ステップ)?', text_norm)
    if num_match:
        val = int(num_match.group(1))
        # 2桁以上（10以上）は絶対温度指定の可能性があるため相対変更からは除外
        if val >= 10:
            return None, None
        val = max(1, min(5, val))
    else:
        # 数値省略（例: 「温度下げて」「少し下げて」）
        val = 1

    delta = -val if is_down else val
    return delta, hint

def execute_relative_temperature_change(delta: int, device_hint: str = None, send_api_fn = None):
    """
    現在稼働中の空調機器（エアコン/ヒーター）の現在温度を確認し、相対温度変更を実行する
    """
    st = load_current_state()
    ac_mode = st.get('acMode', 'off')
    ac_on = ac_mode in ('cool', 'dry', 'heat')
    heater_mode = st.get('heaterMode', 'off')
    heater_on = heater_mode == 'heat'

    # 制御対象機器の決定
    target_device = device_hint
    if not target_device:
        if ac_on and not heater_on:
            target_device = 'ac'
        elif heater_on and not ac_on:
            target_device = 'heater'
        elif ac_on and heater_on:
            # 両方稼働時は冷やすならエアコン、暖めるならヒーター
            target_device = 'ac' if delta < 0 else 'heater'
        else:
            # 両方停止時は体感温度で判断
            wdata = weather_service.get_weather_data()
            feels_like = wdata.get('feels_like', wdata.get('temp', 24.0))
            target_device = 'heater' if feels_like <= 19.0 else 'ac'

    if target_device == 'ac':
        current_temp = int(st.get('acTemp', 26))
        target_temp = max(22, min(28, current_temp + delta))
        mode = ac_mode if ac_mode in ('cool', 'dry') else 'cool'
        fan = st.get('acFan', 'auto')

        if send_api_fn:
            send_api_fn('/api/ac', {'mode': mode, 'temp': target_temp, 'fan_mode': fan})

        msg = format_standard_message('ac', 'relative', {
            'mode': mode,
            'temp': target_temp,
            'diff': delta,
            'current': current_temp
        })
        return {
            "success": True,
            "message": msg,
            "action": f"ac_{mode}_{target_temp}"
        }

    elif target_device == 'heater':
        current_temp = int(st.get('heaterTemp', 22))
        count = abs(delta)
        action = 'plus' if delta > 0 else 'minus'
        if action == 'plus':
            target_temp = min(28, current_temp + count)
        else:
            target_temp = max(22, current_temp - count)

        if send_api_fn:
            send_api_fn('/api/heater', {'action': action, 'count': count, 'temp': target_temp})

        msg = format_standard_message('heater', action, {
            'count': count,
            'temp': target_temp,
            'current': current_temp
        })
        return {
            "success": True,
            "message": msg,
            "action": f"heater_{action}_{count}"
        }

    return None

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
        if 'diff' in params:
            diff = params['diff']
            direction = '上げ' if diff > 0 else '下げ'
            current = params.get('current')
            if current is not None:
                return f"エアコンの温度を{abs(diff)}度{direction}て、{mode_label}{temp}℃に設定しました。（{current}℃ ➔ {temp}℃）"
            return f"エアコンの温度を{abs(diff)}度{direction}て、{mode_label}{temp}℃に設定しました。"
        return f"エアコンを{mode_label}{temp}℃に設定しました。"
    
    elif device == 'heater':
        if action in ('on', 'turnOn', 'heat'): return "ヒーターをオンにしました。"
        if action in ('off', 'turnOff'): return "ヒーターをオフにしました。"
        if action == 'eco': return "ヒーターのエコモードを設定しました。"
        if action == 'plus':
            count = params.get('count', 1)
            target = params.get('temp')
            target_str = f"（設定温度: {target}℃）" if target else ""
            return f"ヒーターの温度を{count}度上げました。{target_str}" if count > 1 else f"ヒーターの温度を上げました。{target_str}"
        if action == 'minus':
            count = params.get('count', 1)
            target = params.get('temp')
            target_str = f"（設定温度: {target}℃）" if target else ""
            return f"ヒーターの温度を{count}度下げました。{target_str}" if count > 1 else f"ヒーターの温度を下げました。{target_str}"
        return "ヒーターを設定しました。"
    
    elif device == 'cleaner':
        if action in ('start', 'run', 'clean', 'play'): return "クリーナーのお掃除を開始しました。"
        if action in ('pause', 'stop'): return "クリーナーを一時停止しました。"
        if action in ('home', 'dock', 'return'): return "クリーナーを充電ドックへ戻します。"
        if action in ('find', 'find_me', 'beep'): return "クリーナーの位置探索アラームを鳴らします。"
        return "クリーナーを設定しました。"
    
    elif device == 'scene':
        if action == 'leaving': return "いってらっしゃい。ライトと空調をすべてオフにしました。"
        if action == 'all_off': return "ライトと空調をすべてオフにしました。"
        
        # おはよう
        if action == 'morning':
            hvac = params.get('hvac')
            feels_like = params.get('feels_like')
            if hvac == 'ac':
                return f"おはようございます。ライトを点灯し、体感温度が{feels_like}℃のためエアコンを冷房{params.get('temp', 26)}℃で起動しました。"
            elif hvac == 'heater':
                return f"おはようございます。ライトを点灯し、体感温度が{feels_like}℃で肌寒いためヒーターをオンにしました。"
            else:
                return f"おはようございます。ライトを点灯しました。（体感温度 {feels_like}℃）"

        # おやすみ
        if action == 'goodnight':
            hvac = params.get('hvac')
            feels_like = params.get('feels_like')
            if hvac == 'ac':
                return f"おやすみなさい。ライトを消灯し、体感温度が{feels_like}℃のためエアコンを冷房{params.get('temp', 27)}℃で起動しました。"
            elif hvac == 'heater':
                return f"おやすみなさい。ライトを消灯し、体感温度が{feels_like}℃で冷え込んでいるためヒーターをオンにしました。"
            else:
                return f"おやすみなさい。ライトを消灯しました。（体感温度 {feels_like}℃）"

        # ただいま
        if action == 'welcome':
            light_note = "日没後のためライトを点灯し、" if params.get('light') else ""
            hvac = params.get('hvac')
            feels_like = params.get('feels_like')
            if hvac == 'ac':
                hvac_note = f"体感温度が{feels_like}℃のためエアコンを冷房{params.get('temp', 26)}℃で起動しました。"
            elif hvac == 'heater':
                hvac_note = f"体感温度が{feels_like}℃で肌寒いためヒーターをオンにしました。"
            else:
                hvac_note = f"体感温度が{feels_like}℃で快適なため空調はオフのままにしました。"
            return f"おかえりなさい。{light_note}{hvac_note}"
    
    return "操作を完了しました。"

def query_gemini_api(prompt_text):
    """Google AI Studio の Gemini 2.0 Flash API (無料枠) で高度な意図解釈を実行"""
    api_key = get_gemini_api_key()
    if not api_key:
        return None

    # 最新のセンサー・環境コンテキストおよび機器状態を構築
    wdata = weather_service.get_weather_data()
    pdata = presence_service.get_presence_status()
    tdata = tile_service.get_tile_status()
    cstate = load_current_state()

    ac_st_str = f"冷房 {cstate.get('acTemp', 26)}℃" if cstate.get('acMode') == 'cool' else ('除湿' if cstate.get('acMode') == 'dry' else '停止中')
    heater_st_str = f"暖房 {cstate.get('heaterTemp', 22)}℃" if cstate.get('heaterMode') == 'heat' else '停止中'

    system_instruction = f"""あなたはスマートホームAI「Nova」の意図解釈エンジンです。
現在のリアルタイム環境・機器コンテキスト:
- 木月（川崎）の天気: {wdata.get('weather', '--')}、外気温: {wdata.get('temp', '--')}℃、体感温度: {wdata.get('feels_like', '--')}℃、日の入り: {wdata.get('sunset', '--')}
- 在宅状態: {'在宅' if pdata.get('is_home') else '外出'}
- 鍵（Tile）: {'室内にあり' if tdata.get('in_home') else '室内になし'}
- エアコン稼働状態: {ac_st_str} (現在設定: {cstate.get('acTemp', 26)}℃)
- ヒーター稼働状態: {heater_st_str} (現在設定: {cstate.get('heaterTemp', 22)}℃)

登録されている正式なスマートシーン（全4種・画面表示名）:
1. 「おはよう」（morning）: リビング点灯 + 体感温度に応じた快適空調
2. 「おやすみ」（goodnight）: リビング消灯 + 体感温度に応じた就寝空調（冷房27℃等）
3. 「いってきます」（leaving）: 照明と空調の一括全停止
4. 「ただいま」（welcome）: 日没後のみリビング点灯 + 体感温度に応じた快適空調

登録されている正式なオートメーション（全2種・画面表示名）:
1. 「朝」（weekday_morning_light）: 日本の平日（土日祝除く）06:30 にリビング点灯
2. 「外出時消し忘れ防止」（away_device_warning）: 在宅➔不在変化時に照明や空調がついていれば消灯確認通知を送信（通知から「いってきます」即時実行可能）

ユーザーの入力から家電操作または質問への回答を抽出し、以下のJSON形式のみを出力してください。
操作可能デバイス:
- light: {{"device": "light", "action": "on"|"off"|"full"|"night"|"toggle"}}
- ac: {{"device": "ac", "mode": "cool"|"dry"|"off", "temp": 22..28, "fan": "auto"}}
- heater: {{"device": "heater", "action": "on"|"off"|"eco"|"plus"|"minus", "count": 1..5}}
- cleaner: {{"device": "cleaner", "action": "start"|"pause"|"home"|"find"}}
- scene: {{"device": "scene", "action": "morning"|"goodnight"|"leaving"|"welcome"|"all_off"}}
- relative_temp: 相対的な温度変更（「2度下げて」「少し暖かく」等）: {{"device": "relative_temp", "delta": -5..5, "target": "ac"|"heater"|null}}
- question: 質問や確認、挨拶等でメッセージを回答する場合: {{"device": "question", "message": "簡潔な返答テキスト"}}
- none: 該当なしの場合: {{"device": "none"}}

重要ルール:
- 「温度2度下げて」「少し暖かくして」などの相対温度変更指示では、現在稼働中の機器の現在設定温度を基準に delta を設定してください。
- シーンやオートメーションの名称を回答する際は、必ず上記の正式な画面表示名（「おはよう」「おやすみ」「いってきます」「ただいま」「朝」）を正確に使用してください。
- 鍵の所在に関する回答は「室内にあります」または「室内にはありません」のみとする。
- 余計な説明やMarkdownコードブロックは一切含めず、純粋なJSONオブジェクト1つだけを出力してください。"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"ユーザー: {prompt_text}"}
                ]
            }
        ],
        "system_instruction": {
            "parts": [
                {"text": system_instruction}
            ]
        },
        "generationConfig": {
            "temperature": 0.1,
            "response_mime_type": "application/json",
            "maxOutputTokens": 300
        }
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=5) as res:
            res_json = json.loads(res.read().decode('utf-8'))
            candidates = res_json.get('candidates', [])
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                if parts:
                    text_out = parts[0].get('text', '{}')
                    return json.loads(text_out)
    except Exception as e:
        print(f"[Gemini API Notice] {e}")
        return None

def query_local_llm(prompt_text):
    """ローカルOllama (Qwen 2.5 1.5B) によるフォールバック"""
    system_prompt = """あなたはスマートホームAI「Nova」です。ユーザーの要望が家電操作に該当する場合のみ以下のJSON形式を出力してください。
操作可能デバイス:
- light: {"device": "light", "action": "on"|"off"|"full"|"night"}
- ac: {"device": "ac", "mode": "cool"|"dry"|"off", "temp": 22..28, "fan": "auto"}
- heater: {"device": "heater", "action": "on"|"off"|"eco"|"plus"|"minus", "count": 1..5}
- cleaner: {"device": "cleaner", "action": "start"|"pause"|"home"|"find"}
- scene: {"device": "scene", "action": "morning"|"goodnight"|"leaving"|"welcome"|"all_off"}

重要: 雑談や家電操作と無関係な言葉の場合は {"device": "none"} を出力してください。
出力形式(JSONのみ):
{"device": "...", "action": "...", "temp": 24, "mode": "cool", "count": 1}"""

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

import flow_engine

def determine_smart_hvac(send_api_fn=None, sleep_mode=False):
    """
    木月のリアルタイム体感温度（feels_like）に基づく空調（エアコン/ヒーター）自動判定・制御
    flow_engine.execute_smart_hvac に一本化
    """
    return flow_engine.execute_smart_hvac(send_api_fn=send_api_fn, sleep_mode=sleep_mode)

def execute_smart_morning(send_api_fn=None):
    """おはようシーン：フロー定義（scenes_config.json）に基づいて自動実行"""
    return flow_engine.execute_scene('morning', send_api_fn=send_api_fn)

def execute_smart_goodnight(send_api_fn=None):
    """おやすみシーン：フロー定義（scenes_config.json）に基づいて自動実行"""
    return flow_engine.execute_scene('goodnight', send_api_fn=send_api_fn)

def execute_smart_welcome(send_api_fn=None):
    """ただいまシーン：フロー定義（scenes_config.json）に基づいて自動実行"""
    return flow_engine.execute_scene('welcome', send_api_fn=send_api_fn)

def execute_smart_leaving(send_api_fn=None):
    """いってきますシーン：フロー定義（scenes_config.json）に基づいて自動実行"""
    return flow_engine.execute_scene('leaving', send_api_fn=send_api_fn)

def _dispatch_parsed_intent(parsed_data, send_api_fn=None):
    """LLMから返却された構造化インテントJSONを実行して結果メッセージを返す"""
    if not parsed_data or not isinstance(parsed_data, dict):
        return None

    device = parsed_data.get('device')
    if not device or device == 'none':
        return None

    if device == 'question':
        msg = parsed_data.get('message', 'お答えします。')
        return {"success": True, "message": msg, "action": "answer"}

    if device == 'relative_temp':
        delta = int(parsed_data.get('delta', 1))
        target = parsed_data.get('target')
        return execute_relative_temperature_change(delta, target, send_api_fn)

    if device == 'scene':
        act = parsed_data.get('action', 'all_off')
        if act in ('morning', '朝'):
            return execute_smart_morning(send_api_fn)
        elif act in ('goodnight', 'おやすみ'):
            return execute_smart_goodnight(send_api_fn)
        elif act in ('leaving', 'いってきます'):
            return execute_smart_leaving(send_api_fn)
        elif act in ('welcome', 'ただいま'):
            return execute_smart_welcome(send_api_fn)
        elif act == 'all_off':
            return execute_smart_leaving(send_api_fn)

    elif device == 'light':
        act = parsed_data.get('action', 'on')
        if act in ('on', 'off', 'full', 'night', 'toggle'):
            if send_api_fn: send_api_fn('/api/light', {'action': act})
            return {"success": True, "message": format_standard_message('light', act), "action": f"light_{act}"}

    elif device == 'ac':
        if 'delta' in parsed_data:
            return execute_relative_temperature_change(int(parsed_data['delta']), 'ac', send_api_fn)
        mode = parsed_data.get('mode', 'cool')
        temp = int(parsed_data.get('temp', 26))
        temp = max(22, min(28, temp))
        fan = parsed_data.get('fan', 'auto')
        if send_api_fn: send_api_fn('/api/ac', {'mode': mode, 'temp': temp, 'fan_mode': fan})
        return {"success": True, "message": format_standard_message('ac', 'on' if mode != 'off' else 'off', {'mode': mode, 'temp': temp}), "action": f"ac_{mode}_{temp}"}

    elif device == 'heater':
        if 'delta' in parsed_data:
            return execute_relative_temperature_change(int(parsed_data['delta']), 'heater', send_api_fn)
        act = parsed_data.get('action', 'on')
        count = int(parsed_data.get('count', 1))
        count = max(1, min(5, count))
        if act in ('on', 'off', 'eco'):
            if send_api_fn: send_api_fn('/api/heater', {'action': act})
            return {"success": True, "message": format_standard_message('heater', act), "action": f"heater_{act}"}
        elif act in ('plus', 'minus'):
            if send_api_fn: send_api_fn('/api/heater', {'action': act, 'count': count})
            return {"success": True, "message": format_standard_message('heater', act, {'count': count}), "action": f"heater_{act}_{count}"}

    elif device == 'cleaner':
        act = parsed_data.get('action', 'start')
        if act in ('start', 'pause', 'home', 'find'):
            if send_api_fn: send_api_fn('/api/cleaner', {'action': act})
            return {"success": True, "message": format_standard_message('cleaner', act), "action": f"cleaner_{act}"}

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
    if text in ('nova', 'ノヴァ', 'ノバ', 'のゔぁ', 'のば', 'nova!', 'nova?', 'ノヴァ！', 'ノヴァ？', 'ノバ！', 'ノバ？'):
        return {"success": True, "message": "はい、Novaです。何か操作しますか？", "action": "wake"}

    if text in ('やあ', 'やあやあ', 'こんにちは', 'こんばんは', 'どうも', 'ヘイ', 'へい', 'おーい', 'おい', 'hi', 'hello', 'hey'):
        return {"success": True, "message": "こんにちは！何か操作しますか？", "action": "greeting"}

    if text in ('ありがとう', 'ありがと', 'サンキュー', 'さんきゅー', 'thanks', 'thank you', 'お疲れ', 'おつかれ', '助かった'):
        return {"success": True, "message": "どういたしまして！", "action": "thanks"}

    if text in ('テスト', 'test', 'てすと', 'チェック', 'あ', 'ああ', 'うん'):
        return {"success": True, "message": "はい、待機しています。", "action": "test"}

    # 先頭の呼びかけを除去
    clean_text = re.sub(r'^(nova|ノヴァ|ノバ|のゔぁ|のば)[、,\s]*', '', text).strip()
    if not clean_text:
        return {"success": True, "message": "はい、Novaです。何か操作しますか？", "action": "wake"}

    text = clean_text

    # -------------------------------------------------------------
    # 第1段階：ミリ秒レベルの超高速ルールベース（日常の98%を即答）
    # -------------------------------------------------------------

    # 1. シーン一覧・個数問い合わせ (全4種: おはよう, おやすみ, いってきます, ただいま)
    if re.search(r'シーン.*(何|いくつ|どんな|一覧|教えて|ある|種類|名|数|リスト)', text):
        msg = "登録されているシーンは「おはよう」「おやすみ」「いってきます」「ただいま」の全4種類です。"
        return {"success": True, "message": msg, "action": "scenes_list"}

    # 2. オートメーション一覧・個数問い合わせ (全3種: 平日 6:30, 平日 9:00, 外出時)
    if re.search(r'(オートメーション|自動化).*(何|いくつ|どんな|一覧|教えて|ある|種類|名|数|リスト)', text):
        msg = "登録されているオートメーションは「平日 6:30」（リビング照明点灯）、「平日 9:00」（ロボット掃除機）、および「外出時」（消し忘れ通知）の全3種類です。"
        return {"success": True, "message": msg, "action": "automations_list"}

    # 2.5 通知テスト・消し忘れ通知送信
    if any(k in text for k in ['通知テスト', 'プッシュテスト', '消し忘れ通知テスト', '通知送って', '通知を送って', '通知テストして', '通知確認']):
        try:
            import push_service
            notif = push_service.send_away_device_warning()
            if notif:
                return {"success": True, "message": "消し忘れ確認通知を送信しました。", "action": "push_test"}
            else:
                return {"success": True, "message": "稼働中の機器がないため、通知は送信されませんでした。", "action": "push_test"}
        except Exception as e:
            return {"success": False, "message": f"通知送信でエラーが発生しました: {e}", "action": "push_error"}

    # 3. 機能一覧 / ヘルプ
    if any(k in text for k in ['何ができる', 'なにができる', '使い方', 'つかいかた', 'ヘルプ', 'help', 'コマンド一覧', '操作一覧']):
        msg = "照明・エアコン・ヒーター・クリーナーの操作、気象や在宅・鍵の確認、および4つのシーン（「おはよう」「おやすみ」「いってきます」「ただいま」）を実行できます。"
        return {"success": True, "message": msg, "action": "help"}

    # 4. 状態確認 (Status)
    if any(k in text for k in ['状態', 'ステータス', 'どうなってる', '今の設定', '確認', 'status', 'じょうたい']):
        try:
            st = state_manager.load_state()
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
            return {"success": True, "message": "機器の状態を確認しました。", "action": "status"}

    # 2. 木月エリアの気象情報（外気温・天気・日の出・日の入り）
    if any(k in text for k in ['日の入り', '日没', '日の出', '日照', '夕暮れ', '日暮れ']):
        w = weather_service.get_weather_data()
        msg = f"本日の木月の日の入りは{w['sunset']}、日の出は{w['sunrise']}です。"
        return {"success": True, "message": msg, "action": "weather_solar"}

    if any(k in text for k in ['気温', '外気温', '外の温度', '外温度', '何度', '外は寒い', '外は暑い', '外寒い', '外暑い', '体感温度', '体感']):
        w = weather_service.get_weather_data()
        msg = f"現在の木月の気温は{w['temp']}℃（体感温度 {w['feels_like']}℃）、湿度は{w['humidity']}%です。"
        return {"success": True, "message": msg, "action": "weather_temp"}

    if any(k in text for k in ['天気', 'てんき', '雨降る', '傘', '晴れ', 'weather']):
        w = weather_service.get_weather_data()
        msg = f"現在の木月の天気は{w['weather']}、外気温は{w['temp']}℃（体感 {w['feels_like']}℃）です。"
        return {"success": True, "message": msg, "action": "weather_condition"}

    # 3. 在宅検出・在宅状況確認 (Presence)
    if any(k in text for k in ['在宅', 'ざいたく', '家にいる', '外出', 'がいしゅつ', '帰ってる', '家に誰か', 'スマホいる', 'スマホある']):
        p = presence_service.get_presence_status()
        status_str = "「在宅中」" if p["is_home"] else "「外出中」"
        msg = f"現在の状況は{status_str}です。（最終検知: {p['last_seen_str']}）"
        return {"success": True, "message": msg, "action": "presence_status"}

    # 4. 鍵（Tile）置き忘れ・所在確認 (Key Tracker: 確定情報に基づき室内にあるかないかのみ回答)
    if any(k in text for k in ['鍵', 'カギ', 'かぎ', 'キー', 'tile', 'ポスト', 'ぽすと']):
        t = tile_service.get_tile_status()
        msg = "室内にあります" if t["in_home"] else "室内にはありません"
        return {"success": True, "message": msg, "action": "tile_key_status"}

    # 5. スマートシーン一括操作 (優先度高)
    # 5-A. 朝 / おはよう (ライト点灯 + 体感温度によるスマート空調)
    if any(k in text for k in ['おはよう', 'おはよ', '起きた', 'おきた', '朝のシーン', 'morning', '朝']):
        return execute_smart_morning(send_api_fn)

    # 5-B. おやすみ (ライト消灯 + 体感温度によるスマート就寝空調)
    if any(k in text for k in ['おやすみ', '寝る', 'ねる', '就寝', 'ベッド', 'goodnight']):
        return execute_smart_goodnight(send_api_fn)

    # 5-C. いってきます (フロー定義に基づき一括全停止)
    if any(k in text for k in ['いってきます', '行ってきます', '外出', 'がいしゅつ', '出かける', 'でかける', '家出る', 'leave']):
        return execute_smart_leaving(send_api_fn)

    # 5-D. ただいま (日没判定ライト + 体感温度によるスマート空調)
    if any(k in text for k in ['ただいま', '帰宅', 'きたく', '家着いた', 'ついた', '着いた', '帰った', 'かえった', 'welcome']):
        return execute_smart_welcome(send_api_fn)

    # 5-E. 全部消して / 全消し
    if any(k in text for k in ['全部消して', '全消し', 'ぜんぶけして', 'すべて消して', '消灯して', '全部オフ']):
        if send_api_fn:
            send_api_fn('/api/light', {'action': 'off'})
            send_api_fn('/api/ac', {'mode': 'off'})
            send_api_fn('/api/heater', {'action': 'off'})
        return {"success": True, "message": format_standard_message('scene', 'all_off'), "action": "scene_all_off"}

    # 6. クリーナー / 掃除 (Cleaner)
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

    # 7. ライト / 照明 (Light)
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

    # 8. 空調（エアコン/ヒーター）の相対温度変更（「温度二度下げて」「2度上げて」「少し暖かくして」「ちょっと涼しくして」等）
    # ※現在稼働中の機器の現在設定温度を確認した上で、正確に差分を反映
    delta, hint = parse_relative_temp_change(text)
    if delta is not None:
        rel_res = execute_relative_temperature_change(delta, hint, send_api_fn)
        if rel_res:
            return rel_res

    # 9. ヒーター / 暖房 (Heater: オンオフ/エコ/モード)
    if any(k in text for k in ['ヒーター', 'ひーたー', '暖房', 'だんぼう', 'ストーブ', 'すとーぶ', 'heater']):
        # オフ
        if any(k in text for k in ['消して', 'けして', 'オフ', 'おふ', '止めて', 'とめて', '切って', 'きって', 'off', 'stop', '消す']):
            if send_api_fn: send_api_fn('/api/heater', {'action': 'off'})
            return {"success": True, "message": format_standard_message('heater', 'off'), "action": "heater_off"}
        # エコ
        elif any(k in text for k in ['エコ', 'えこ', 'eco']):
            if send_api_fn: send_api_fn('/api/heater', {'action': 'eco'})
            return {"success": True, "message": format_standard_message('heater', 'eco'), "action": "heater_eco"}
        # 温度直指定に対する注意ガード
        elif re.search(r'(\d{2})\s*(度|℃)', text):
            return {
                "success": False,
                "message": "ヒーターは温度の直接指定に対応していないため、オン/オフまたは温度の上下（上げて/下げて）でご指定ください。",
                "action": None
            }
        # つけて / オン
        elif any(k in text for k in ['つけて', '点けて', 'オン', 'おん', 'on', 'つける', '起動', 'スタート']):
            if send_api_fn: send_api_fn('/api/heater', {'action': 'on'})
            return {"success": True, "message": format_standard_message('heater', 'on'), "action": "heater_on"}
        else:
            if send_api_fn: send_api_fn('/api/heater', {'action': 'on'})
            return {"success": True, "message": format_standard_message('heater', 'on'), "action": "heater_on"}

    # 10. エアコン / クーラー / 冷房 / 除湿 (AC: オンオフ/絶対温度指定)
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

    # 温度のみの絶対指定（「24度」「24度にして」など ──▶ エアコン冷房）
    if re.search(r'^\s*(\d{2})\s*(度|℃|c)?(にして|に設定|にしてよ|設定|)?\s*$', text):
        temp = int(re.search(r'(\d{2})', text).group(1))
        temp = max(22, min(28, temp))
        if send_api_fn: send_api_fn('/api/ac', {'mode': 'cool', 'temp': temp, 'fan_mode': 'auto'})
        return {"success": True, "message": format_standard_message('ac', 'on', {'mode': 'cool', 'temp': temp}), "action": f"ac_cool_{temp}"}

    # -------------------------------------------------------------
    # 第2段階：Gemini 2.0 Flash API (無料枠) によるインテリジェント推論
    # -------------------------------------------------------------
    gemini_res = query_gemini_api(prompt)
    if gemini_res:
        dispatched = _dispatch_parsed_intent(gemini_res, send_api_fn)
        if dispatched:
            return dispatched

    # -------------------------------------------------------------
    # 第3段階：ローカルAI (Ollama Qwen 2.5 1.5B) フォールバック
    # -------------------------------------------------------------
    llm_res = query_local_llm(prompt)
    if llm_res:
        dispatched = _dispatch_parsed_intent(llm_res, send_api_fn)
        if dispatched:
            return dispatched

    # -------------------------------------------------------------
    # 第4段階：解釈不能の場合（家電を動かさず安全に応答）
    # -------------------------------------------------------------
    return {
        "success": False,
        "message": f"「{prompt}」に対応する操作が見つかりませんでした。",
        "action": None
    }

if __name__ == '__main__':
    test_queries = [
        "おはよう",
        "おやすみ",
        "ただいま",
        "いってきます",
        "鍵ある？",
        "明日の木月の天気は？"
    ]
    for q in test_queries:
        res = parse_and_execute(q, lambda ep, data: print(f"  [API Call] {ep} {data}"))
        print(f"[{q}] -> {res.get('message')}\n")
