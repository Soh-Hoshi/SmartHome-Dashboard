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
        "message": "",
        "actions": [
            {"id": "act_leave", "title": "いってきます", "command": "いってきます"},
            {"id": "act_reply", "title": "Novaへ指示", "reply": True, "reply_placeholder": "Novaに指示..."},
            {"id": "act_dismiss", "title": "閉じる", "dismiss": True}
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

def test_8_crawler_blocking_and_auth():
    print("[8/8] Testing crawler blocking & key/cookie authentication...")
    import auth_service
    key = auth_service.get_access_key()

    # 1. クローラー模倣 (外部IP、キー・Cookieなし) -> 403 遮断
    req_crawler = urllib.request.Request(f"{BASE_URL}/dashboard/", headers={"X-Forwarded-For": "198.51.100.22"})
    try:
        with urllib.request.urlopen(req_crawler, timeout=5) as res:
            assert False, f"Crawler was not blocked! Status: {res.status}"
    except urllib.error.HTTPError as e:
        assert e.code == 403, f"Expected 403 for crawler, got {e.code}"

    # 2. クローラーによる API 操作リクエスト -> 403 遮断
    req_crawler_post = urllib.request.Request(
        f"{BASE_URL}/api/light",
        data=b'{"action":"toggle"}',
        headers={"X-Forwarded-For": "198.51.100.22", "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req_crawler_post, timeout=5) as res:
            assert False, f"Crawler POST was not blocked! Status: {res.status}"
    except urllib.error.HTTPError as e:
        assert e.code == 403, f"Expected 403 for crawler POST, got {e.code}"

    # 3. 正しい合言葉による初回アクセス -> 302 リダイレクト & Set-Cookie
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, hdrs, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    try:
        res = opener.open(urllib.request.Request(f"{BASE_URL}/dashboard/?key={key}", headers={"X-Forwarded-For": "198.51.100.22"}))
        status, hdrs = res.status, res.headers
    except urllib.error.HTTPError as e:
        status, hdrs = e.code, e.headers

    assert status == 302, f"Expected 302 on ?key=, got {status}"
    cookie_hdr = hdrs.get("Set-Cookie", "")
    assert "sh_auth=" in cookie_hdr, "Set-Cookie missing sh_auth"

    # 4. Cookie 付きでの継続アクセス -> 200 OK
    cookie_val = [p.split(';')[0] for p in cookie_hdr.split(', ') if 'sh_auth=' in p][0]
    req_cookie = urllib.request.Request(f"{BASE_URL}/dashboard/", headers={"X-Forwarded-For": "198.51.100.22", "Cookie": cookie_val})
    with urllib.request.urlopen(req_cookie, timeout=5) as res:
        assert res.status == 200, f"Expected 200 with Cookie, got {res.status}"

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
    test_8_crawler_blocking_and_auth()
    print("=== ALL TESTS PASSED SUCCESSFULLY ===")
