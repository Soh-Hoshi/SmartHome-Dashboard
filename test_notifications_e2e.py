#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite: SmartHome Notification System & SSE Stream Integrity
Tests standard notifications, in-place updates, progress bars, action schemas,
fallback polling, Assistant API actions, and concurrent real-time SSE stream delivery.
"""
import sys
import time
import json
import threading
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8080"

def post_json(endpoint: str, data: dict):
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=5) as res:
        return json.loads(res.read().decode("utf-8"))

def get_json(endpoint: str):
    req = urllib.request.Request(f"{BASE_URL}{endpoint}")
    with urllib.request.urlopen(req, timeout=5) as res:
        return json.loads(res.read().decode("utf-8"))

def test_1_standard_notification():
    print("[1/7] Testing standard notification dispatch...")
    res = post_json("/api/notify", {
        "title": "テスト通知",
        "message": "ユニットテストメッセージ",
        "priority": "high"
    })
    assert res.get("status") == "success"
    n = res["notification"]
    assert n["title"] == "テスト通知"
    assert n["body"] == "ユニットテストメッセージ"
    assert n["id"].startswith("notif_")
    print("  -> Passed.")

def test_2_inplace_and_progress():
    print("[2/7] Testing in-place update & progress bar schema...")
    fixed_id = "test_progress_fixed_id"
    for p in [20, 50, 100]:
        res = post_json("/api/notify", {
            "id": fixed_id,
            "title": "清掃中",
            "message": f"進行状況 {p}%",
            "progress": {"current": p, "max": 100, "indeterminate": False},
            "ongoing": (p < 100)
        })
        n = res["notification"]
        assert n["id"] == fixed_id
        assert n["progress"]["current"] == p
        assert n["ongoing"] == (p < 100)
    print("  -> Passed.")

def test_3_action_buttons_and_direct_reply():
    print("[3/7] Testing action buttons & Direct Reply schema...")
    res = post_json("/api/notify", {
        "id": "away_test",
        "title": "お出かけですか？",
        "message": "照明が点灯中です",
        "actions": [
            {"id": "act_leave", "title": "🚪 いってきます", "command": "いってきます"},
            {"id": "act_reply", "title": "💬 指示", "reply": True, "reply_placeholder": "Novaに指示..."},
            {"id": "act_dismiss", "title": "そのまま", "dismiss": True}
        ]
    })
    actions = res["notification"]["actions"]
    assert len(actions) == 3
    assert actions[0]["command"] == "いってきます"
    assert actions[1]["reply"] is True
    assert actions[2]["dismiss"] is True
    print("  -> Passed.")

def test_4_assistant_action_execution():
    print("[4/7] Testing Assistant API action execution (/api/assistant)...")
    res = post_json("/api/assistant", {"prompt": "いってきます"})
    assert res.get("success") is True
    assert len(res.get("message", "")) > 0
    print(f"  -> Passed (Response: {res.get("message")}).")

def test_5_fallback_polling():
    print("[5/7] Testing fallback polling (/api/notifications/poll)...")
    now_ts = time.time() - 10.0
    res = get_json(f"/api/notifications/poll?since={now_ts}")
    assert res.get("status") == "success"
    assert "server_time" in res
    assert isinstance(res.get("notifications"), list)
    assert len(res["notifications"]) > 0
    print("  -> Passed.")

def test_6_sse_concurrent_realtime_stream():
    print("[6/7] Testing real-time SSE stream with concurrent clients...")
    received_events = []
    stream_started = threading.Event()

    def sse_listener():
        req = urllib.request.Request(f"{BASE_URL}/api/notifications/stream")
        with urllib.request.urlopen(req, timeout=10) as res:
            l1 = res.readline().decode("utf-8").strip()
            l2 = res.readline().decode("utf-8").strip()
            _ = res.readline()
            assert l1 == "event: connected"
            assert "connected" in l2
            conn_data = json.loads(l2.replace("data:", "").strip())
            assert "server_time" in conn_data
            stream_started.set()

            while len(received_events) < 1:
                line = res.readline().decode("utf-8").strip()
                if line.startswith("data:"):
                    received_events.append(line[5:].strip())
                    break

    thread = threading.Thread(target=sse_listener, daemon=True)
    thread.start()
    assert stream_started.wait(timeout=3), "SSE stream failed to connect"

    test_id = f"realtime_sse_{int(time.time())}"
    post_json("/api/notify", {
        "id": test_id,
        "title": "リアルタイムテスト",
        "message": "SSEストリーム配信テスト"
    })

    thread.join(timeout=5)
    assert len(received_events) == 1, "Failed to receive SSE event in real-time"
    notif_data = json.loads(received_events[0])
    assert notif_data.get("id") == test_id
    assert notif_data.get("title") == "リアルタイムテスト"
    print("  -> Passed.")

def test_7_subpath_routing_compatibility():
    print("[7/7] Testing /dashboard subpath API compatibility...")
    res = post_json("/dashboard/api/notify", {
        "title": "サブパステスト",
        "message": "Tailscale /dashboard 互換性テスト"
    })
    assert res.get("status") == "success"
    poll_res = get_json(f"/dashboard/api/notifications/poll?since={time.time() - 5}")
    assert poll_res.get("status") == "success"
    print("  -> Passed.")

if __name__ == "__main__":
    print("=== SmartHome Notification & SSE Verification Test Suite ===")
    test_1_standard_notification()
    test_2_inplace_and_progress()
    test_3_action_buttons_and_direct_reply()
    test_4_assistant_action_execution()
    test_5_fallback_polling()
    test_6_sse_concurrent_realtime_stream()
    test_7_subpath_routing_compatibility()
    print("=== ALL TESTS PASSED SUCCESSFULLY ===")
