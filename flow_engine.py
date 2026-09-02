#!/usr/bin/env python3
"""
Flow Execution Engine (SSOT: Single Source of Truth)
Executes scenes and automations directly based on their declarative flow definitions,
and automatically generates deterministic, natural response messages from execution results.
"""

import os
import json
import time
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

def evaluate_condition(step, context):
    """
    ステップの実行条件を評価 (eval_rule または condition)
    """
    eval_rule = step.get("eval_rule")
    if not eval_rule:
        # eval_rule がない場合は無条件実行
        return True

    feels_like = context.get("feels_like", 24.0)
    temp = context.get("temp", 24.0)
    is_day = context.get("is_day", True)

    eval_env = {
        "feels_like": feels_like,
        "temp": temp,
        "is_day": is_day
    }

    try:
        # 安全な評価環境で条件式を実行
        return bool(eval(eval_rule, {"__builtins__": None}, eval_env))
    except Exception as e:
        print(f"[FlowEngine Eval Error] rule='{eval_rule}': {e}")
        return False

def execute_flow(flow_steps, send_api_fn=None):
    """
    フロー定義配列を逐次評価・実行し、実行されたアクション結果のリストを返す
    """
    context = {}
    executed_steps = []

    for step in flow_steps:
        target = step.get("target")
        action = step.get("action")
        step_type = step.get("type", "device")

        # 1. システム情報取得ステップ
        if step.get("system") == "weather" or target == "気象":
            wdata = weather_service.get_weather_data()
            context["feels_like"] = wdata.get("feels_like", wdata.get("temp", 24.0))
            context["temp"] = wdata.get("temp", 24.0)
            context["is_day"] = wdata.get("is_day", True)
            context["weather_desc"] = wdata.get("weather_desc", "晴れ")
            continue

        # 2. 条件評価
        should_run = evaluate_condition(step, context)
        if not should_run:
            continue

        # 3. IF分岐ステップ (条件判定)
        if step_type == "if" or target == "分岐":
            # 機器が1つでもオンか判定
            if os.path.exists(STATE_FILE):
                try:
                    with open(STATE_FILE, "r", encoding="utf-8") as f:
                        st = json.load(f)
                    has_on = (
                        st.get("lightOn", False) or
                        st.get("acMode", "off") != "off" or
                        st.get("heaterMode", "off") != "off"
                    )
                    if has_on:
                        executed_steps.append(step)
                except Exception:
                    pass
            continue

        # 4. 通知ステップ
        if target == "通知":
            try:
                import push_service
                push_service.send_away_device_warning("照明・空調")
                executed_steps.append(step)
            except Exception as e:
                print(f"[FlowEngine Push Error] {e}")
            continue

        # 5. 通常デバイス制御ステップ
        api_path = step.get("api")
        payload = step.get("payload")

        if api_path and payload and send_api_fn:
            try:
                send_api_fn(api_path, payload)
            except Exception as e:
                print(f"[FlowEngine API Error] {api_path}: {e}")

        executed_steps.append(step)

    return {
        "context": context,
        "executed_steps": executed_steps
    }

def generate_scene_message(scene_id, scene_name, flow_result):
    """
    実行結果から自動的・決定論的に自然で正確な報告メッセージを生成
    """
    context = flow_result.get("context", {})
    executed = flow_result.get("executed_steps", [])
    feels_like = context.get("feels_like")

    # 実行された各デバイスのアクションを抽出
    light_act = next((s["action"] for s in executed if s.get("target") == "リビング"), None)
    ac_act = next((s["action"] for s in executed if s.get("target") == "エアコン"), None)
    heater_act = next((s["action"] for s in executed if s.get("target") == "ヒーター"), None)

    if scene_id == "morning":
        parts = ["おはようございます。"]
        if light_act == "オン":
            parts.append("照明を点灯しました。")
        if ac_act:
            parts.append(f"体感温度{feels_like:.1f}℃のため、エアコンを{ac_act}で運転開始しました。")
        elif heater_act:
            parts.append(f"体感温度{feels_like:.1f}℃のため、ヒーターをオンにしました。")
        else:
            parts.append(f"体感温度{feels_like:.1f}℃で快適なため、空調は停止のままです。")
        return "".join(parts)

    if scene_id == "goodnight":
        parts = ["おやすみなさい。"]
        if light_act == "オフ":
            parts.append("照明を消灯しました。")
        if ac_act:
            parts.append(f"体感温度{feels_like:.1f}℃のため、就寝用にエアコンを{ac_act}に設定しました。")
        elif heater_act:
            parts.append(f"体感温度{feels_like:.1f}℃のため、ヒーターをオンにしました。")
        else:
            parts.append("空調をオフにしました。")
        parts.append("良い夢を。")
        return "".join(parts)

    if scene_id == "leaving":
        return "いってらっしゃい！すべての照明と空調を停止しました。お気をつけて！"

    if scene_id == "welcome":
        parts = ["おかえりなさい！"]
        if light_act == "オン":
            parts.append("日没後のため照明を点灯しました。")
        else:
            parts.append("日没前のため照明はオフのままです。")
        if ac_act:
            parts.append(f"体感温度{feels_like:.1f}℃のため、エアコンを{ac_act}で運転開始しました。")
        elif heater_act:
            parts.append(f"体感温度{feels_like:.1f}℃のため、ヒーターをオンにしました。")
        return "".join(parts)

    return f"{scene_name}のフローを実行しました。"

def execute_scene(scene_id, send_api_fn=None):
    """
    指定されたシーンIDのフローを実行し、結果メッセージを返す
    """
    scenes = load_scenes()
    scene = next((s for s in scenes if s.get("id") == scene_id), None)
    if not scene:
        return {"success": False, "message": f"シーン '{scene_id}' が見つかりません。"}

    flow_steps = scene.get("flow", [])
    flow_result = execute_flow(flow_steps, send_api_fn=send_api_fn)
    message = generate_scene_message(scene_id, scene.get("name", scene_id), flow_result)

    return {
        "success": True,
        "scene_id": scene_id,
        "scene_name": scene.get("name"),
        "message": message,
        "executed_steps": flow_result.get("executed_steps", [])
    }
