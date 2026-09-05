#!/usr/bin/env python3
"""
Lightweight Live-Reload HTTP Server for SmartHome Dashboard
Supports serving from root (/) and subpaths (/dashboard/) over Tailscale HTTPS.
"""

import os
import sys
import time
import io
import json
import socket
import queue
import urllib.parse
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from concurrent.futures import ThreadPoolExecutor

import state_manager
import switchbot_client
import eufy_client
import presence_service
import tile_service
import automation_service
import weather_service
import assistant_engine
import flow_engine
import push_service
import usb_service
import pc_service
import auth_service


PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# バックグラウンドタスク用スレッドプール (最大8並列)
_bg_executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="SmartHomeWorker")

# LiveReload クライアント管理
clients = []
clients_lock = threading.Lock()
last_mtime = 0

def get_latest_mtime():
    max_m = 0
    for root, _, files in os.walk(DIRECTORY):
        for f in files:
            if f.endswith(('.html', '.css', '.js', '.png', '.jpg', '.svg', '.json')) and not f.endswith(('weather_cache.json', 'server.log', 'state.json')):
                try:
                    p = os.path.join(root, f)
                    m = os.path.getmtime(p)
                    if m > max_m:
                        max_m = m
                except OSError:
                    pass
    return max_m

def file_watcher():
    global last_mtime
    last_mtime = get_latest_mtime()
    while True:
        time.sleep(0.5)
        current_m = get_latest_mtime()
        if current_m > last_mtime:
            last_mtime = current_m
            with clients_lock:
                to_remove = []
                for q in clients:
                    try:
                        q.append("reload")
                    except Exception:
                        to_remove.append(q)
                for q in to_remove:
                    if q in clients:
                        clients.remove(q)

LIVE_RELOAD_SCRIPT = b"""
<script>
(() => {
  let es;
  function connect() {
    const basePath = window.location.pathname.startsWith('/dashboard') ? '/dashboard' : '';
    es = new EventSource(basePath + '/__livereload__');
    es.onmessage = (e) => {
      if (e.data === 'reload') {
        console.log('[LiveReload] File changed, reloading...');
        location.reload();
      }
    };
    es.onerror = () => {
      es.close();
      setTimeout(connect, 1500);
    };
  }
  connect();
})();
</script>
</body>
"""

# =======================================================================
# デバイス制御コアロジック (内部API呼び出しとHTTPリクエストで完全共通化)
# =======================================================================

def execute_light_command(action: str) -> dict:
    """照明制御を実行し、最新状態を返す"""
    current_state = state_manager.load_state()
    if action in ('on', 'turnOn', 'full', 'night'):
        current_state['lightOn'] = True
        if action == 'full':
            current_state['lightFull'] = True
            current_state['lightNight'] = False
        elif action == 'night':
            current_state['lightNight'] = True
            current_state['lightFull'] = False
    elif action in ('off', 'turnOff'):
        current_state['lightOn'] = False
        current_state['lightFull'] = False
        current_state['lightNight'] = False
    elif action == 'toggle':
        current_state['lightOn'] = not current_state.get('lightOn', False)
        action = 'turnOn' if current_state['lightOn'] else 'turnOff'
        if not current_state['lightOn']:
            current_state['lightFull'] = False
            current_state['lightNight'] = False

    saved_state = state_manager.save_state(current_state)

    def _send():
        try:
            switchbot_client.control_light(action)
        except Exception as e:
            print(f"[Light Control Error] {e}")

    _bg_executor.submit(_send)
    return {"status": "success", "message": f"Light command dispatched ({action})", "state": saved_state}

def execute_ac_command(mode: str = 'cool', temp: int = 26, fan_mode: str = 'auto') -> dict:
    """エアコン制御を実行し、最新状態を返す"""
    temp = max(22, min(28, int(temp)))
    current_state = state_manager.load_state()
    current_state['acMode'] = mode
    current_state['acTemp'] = temp
    current_state['acFan'] = fan_mode
    saved_state = state_manager.save_state(current_state)

    def _send():
        try:
            switchbot_client.control_ac(mode, temp, fan_mode)
        except Exception as e:
            print(f"[AC Control Error] {e}")

    _bg_executor.submit(_send)
    return {"status": "success", "message": f"AC command dispatched ({mode}, {temp}C, {fan_mode})", "state": saved_state}

def execute_heater_command(action: str = 'toggle', count: int = 1, temp: int = None, eco: bool = None) -> dict:
    """ヒーター制御を実行し、最新状態を返す"""
    count = max(1, min(10, int(count)))
    current_state = state_manager.load_state()

    if action in ('on', 'turnOn', 'heat'):
        current_state['heaterMode'] = 'heat'
    elif action in ('off', 'turnOff'):
        current_state['heaterMode'] = 'off'
    elif action == 'toggle':
        current_state['heaterMode'] = 'off' if current_state.get('heaterMode') == 'heat' else 'heat'
        action = 'turnOn' if current_state['heaterMode'] == 'heat' else 'turnOff'
    elif action in ('eco', 'エコ'):
        current_state['heaterEco'] = eco if eco is not None else not current_state.get('heaterEco', False)
    elif action in ('plus', 'minus'):
        current_temp = current_state.get('heaterTemp', 22)
        if action == 'plus':
            current_state['heaterTemp'] = min(28, current_temp + count)
        else:
            current_state['heaterTemp'] = max(22, current_temp - count)

    if temp is not None:
        current_state['heaterTemp'] = int(temp)

    saved_state = state_manager.save_state(current_state)

    def _send():
        try:
            for i in range(count):
                switchbot_client.control_heater(action)
                if i < count - 1:
                    time.sleep(0.5)
        except Exception as e:
            print(f"[Heater Control Error] {e}")

    _bg_executor.submit(_send)
    return {"status": "success", "message": f"Heater command dispatched ({action}, count={count})", "state": saved_state}

def execute_cleaner_command(action: str = 'start', speed: str = None) -> dict:
    """クリーナー制御を実行し、最新状態を返す"""
    current_state = state_manager.load_state()

    if action in ('start', 'play', 'resume'):
        current_state['cleanerStatus'] = 'running'
        current_state['cleanerPlay'] = True
    elif action in ('pause',):
        current_state['cleanerStatus'] = 'standby'
        current_state['cleanerPlay'] = False
    elif action in ('stop', 'dock', 'home', 'return'):
        current_state['cleanerStatus'] = 'recharge'
        current_state['cleanerPlay'] = False
    elif action == 'speed' and speed:
        current_state['cleanerSpeed'] = speed

    saved_state = state_manager.save_state(current_state)

    def _send():
        try:
            client = eufy_client.EufyG30Client()
            if action in ('start', 'play', 'resume'):
                client.play()
            elif action in ('pause',):
                client.pause()
            elif action in ('stop', 'dock', 'home', 'return'):
                client.return_to_dock()
            elif action == 'speed' and speed:
                client.set_clean_speed(speed)
            elif action in ('find_me', 'find', 'beep'):
                client.find_robot()
        except Exception as e:
            print(f"[Cleaner Control Error] {e}")

    _bg_executor.submit(_send)
    return {"status": "success", "message": f"Cleaner command dispatched ({action})", "state": saved_state}

def dispatch_internal_api(endpoint: str, payload: dict):
    """内部（フローエンジン・アシスタント等）から家電操作を実行する共通エントリーポイント"""
    if endpoint == '/api/light':
        return execute_light_command(payload.get('action', 'toggle'))
    elif endpoint == '/api/ac':
        return execute_ac_command(payload.get('mode', 'cool'), payload.get('temp', 26), payload.get('fan_mode', 'auto'))
    elif endpoint == '/api/heater':
        return execute_heater_command(payload.get('action', 'toggle'), payload.get('count', 1), payload.get('temp'), payload.get('eco'))
    elif endpoint == '/api/cleaner':
        return execute_cleaner_command(payload.get('action', 'start'), payload.get('speed'))
    elif endpoint == '/api/usb':
        action = payload.get('action')
        if action == 'on':
            return {"status": "success", "power": usb_service.set_usb_power(True)}
        elif action == 'off':
            return {"status": "success", "power": usb_service.set_usb_power(False)}
    elif endpoint in ('/api/pc', '/api/pc/boot', '/api/pc/shutdown', '/api/pc/os'):
        action = payload.get('action')
        target_os = payload.get('target_os') or payload.get('os')
        if endpoint == '/api/pc/os' or action in ('set_os', 'select_os'):
            return pc_service.set_target_os(target_os or 'Windows')
        elif endpoint == '/api/pc/boot' or action in ('boot', 'on', 'start'):
            return pc_service.boot_pc()
        elif endpoint == '/api/pc/shutdown' or action in ('shutdown', 'off', 'stop'):
            return pc_service.shutdown_pc()
        else:
            return pc_service.toggle_pc()
    elif endpoint in ('/api/notify', '/api/notification'):
        ongoing = payload.get('ongoing', False)
        auto_cancel = payload.get('auto_cancel', not ongoing)
        notif = push_service.push_notification(
            title=payload.get('title', 'SmartHome'),
            body=payload.get('message') or payload.get('body', ''),
            priority=payload.get('priority', 'high'),
            actions=payload.get('actions', []),
            notif_id=payload.get('id'),
            progress=payload.get('progress'),
            ongoing=ongoing,
            auto_cancel=auto_cancel,
            data=payload.get('data'),
            tag=payload.get('tag')
        )
        return {"status": "success", "notification": notif}
    return {"status": "error", "message": f"Unknown internal endpoint {endpoint}"}



# =======================================================================
# HTTP リクエストハンドラー & ルーティング
# =======================================================================

class LiveReloadHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def send_json_response(self, data, status=HTTPStatus.OK):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(body)

    def send_unauthorized(self, reason: str = ""):
        msg = b"403 Forbidden: Access denied. Valid access key or session cookie required.\n"
        self.send_response(HTTPStatus.FORBIDDEN)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(msg)))
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.end_headers()
        self.wfile.write(msg)

    def send_auth_redirect(self, clean_url: str, cookie_val: str):
        self.send_response(HTTPStatus.FOUND)
        self.send_header('Location', clean_url or '/dashboard/')
        self.send_header('Set-Cookie', auth_service.build_cookie_header(cookie_val, secure=True))
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, HEAD')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Access-Key')
        self.end_headers()

    def do_HEAD(self):
        auth = auth_service.check_request_auth(self.headers, self.client_address, self.path)
        if not auth['authenticated']:
            return self.send_unauthorized(auth.get('reason'))
        return super().do_HEAD()

    def do_GET(self):
        # 認証チェック (外部クローラー遮断 ＆ 合言葉/Cookie/ローカル判定)
        auth = auth_service.check_request_auth(self.headers, self.client_address, self.path)
        if not auth['authenticated']:
            print(f"[AUTH DENIED] path={self.path} client={self.client_address} reason={auth.get('reason')} xff={self.headers.get('X-Forwarded-For')}")
            return self.send_unauthorized(auth.get('reason'))

        print(f"[AUTH OK] path={self.path} client={self.client_address} reason={auth.get('reason')}")

        # ?key=合言葉 による初回アクセス時は、永続Cookieを発行して綺麗なURLへリダイレクト
        if auth.get('set_cookie') and auth.get('clean_url') is not None:
            return self.send_auth_redirect(auth['clean_url'], auth['cookie_value'])

        parsed = urllib.parse.urlparse(self.path)
        clean_path = parsed.path
        if clean_path.startswith('/dashboard'):
            clean_path = clean_path[len('/dashboard'):] or '/'
        query_params = urllib.parse.parse_qs(parsed.query)

        # LiveReload SSE
        if clean_path == '/__livereload__':
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            queue_item = []
            with clients_lock:
                clients.append(queue_item)
            try:
                self.wfile.write(b"data: connected\n\n")
                self.wfile.flush()
                last_ping = time.time()
                while True:
                    time.sleep(0.2)
                    if queue_item:
                        msg = queue_item.pop(0)
                        self.wfile.write(f"data: {msg}\n\n".encode('utf-8'))
                        self.wfile.flush()
                    elif time.time() - last_ping > 20:
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
                        last_ping = time.time()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                with clients_lock:
                    if queue_item in clients:
                        clients.remove(queue_item)
            return

        # NovaAssist & Notification SSE Stream
        if clean_path == '/api/notifications/stream':
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache, no-transform')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('X-Accel-Buffering', 'no')
            self.end_headers()

            q = push_service.register_sse_client()
            try:
                conn_payload = json.dumps({"status": "connected", "server_time": time.time()})
                self.wfile.write(f"event: connected\ndata: {conn_payload}\n\n".encode('utf-8'))
                self.wfile.flush()
                while True:
                    try:
                        notif = q.get(timeout=15)
                        payload = json.dumps(notif, ensure_ascii=False)
                        self.wfile.write(f"event: notification\ndata: {payload}\n\n".encode('utf-8'))
                        self.wfile.flush()
                    except queue.Empty:
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, socket.error):
                pass
            finally:
                push_service.unregister_sse_client(q)
            return

        # Notification Polling Fallback
        if clean_path == '/api/notifications/poll':
            try:
                since = float(query_params.get('since', [0])[0])
            except (ValueError, TypeError):
                since = 0.0
            notifs = push_service.get_notifications_since(since)
            return self.send_json_response({
                "status": "success",
                "notifications": notifs,
                "server_time": time.time()
            })

        # GET API ルーティング
        get_routes = {
            '/api/state': lambda: {"status": "success", "state": state_manager.load_state()},
            '/api/weather': lambda: {"status": "success", "weather": weather_service.get_weather_data()},
            '/api/presence': lambda: {"status": "success", "presence": presence_service.get_presence_status()},
            '/api/tile': lambda: {"status": "success", "tile": tile_service.get_tile_status()},
            '/api/automations': lambda: {"status": "success", "automations": automation_service.load_automations()},
            '/api/scenes': lambda: {"status": "success", "scenes": flow_engine.load_scenes()},
            '/api/usb': lambda: {"status": "success", "power": usb_service.get_usb_power()},
            '/api/pc': lambda: {"status": "success", **pc_service.get_pc_status()},
        }

        if clean_path in get_routes:
            try:
                return self.send_json_response(get_routes[clean_path]())
            except Exception as e:
                return self.send_json_response({"status": "error", "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        if clean_path == '/api/push/vapid-key':
            try:
                keys = push_service.get_or_create_vapid_keys()
                return self.send_json_response({"status": "success", "public_key": keys["public_key"]})
            except Exception as e:
                return self.send_json_response({"status": "error", "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        if clean_path == '/api/cleaner/status':
            try:
                client = eufy_client.EufyG30Client()
                res = client.get_status()
                if res.get("success"):
                    st = state_manager.load_state()
                    st['cleanerStatus'] = res.get('status', 'standby').lower()
                    st['cleanerPlay'] = res.get('play', False)
                    state_manager.save_state(st)
                return self.send_json_response(res)
            except Exception as e:
                return self.send_json_response({"success": False, "error": str(e)})

        # 静的ファイル配信 (/dashboard へのリクエストを / にマップ)
        self.path = clean_path
        return super().do_GET()

    def do_POST(self):
        # 認証チェック (外部クローラー遮断 ＆ 合言葉/Cookie/ローカル判定)
        auth = auth_service.check_request_auth(self.headers, self.client_address, self.path)
        if not auth['authenticated']:
            return self.send_unauthorized(auth.get('reason'))

        parsed = urllib.parse.urlparse(self.path)
        clean_path = parsed.path
        if clean_path.startswith('/dashboard'):
            clean_path = clean_path[len('/dashboard'):] or '/'

        content_len = int(self.headers.get('Content-Length', 0))
        post_body = self.rfile.read(content_len) if content_len > 0 else b'{}'
        try:
            req_data = json.loads(post_body.decode('utf-8'))
        except Exception:
            req_data = {}

        # 0. 通知発行 API (NovaAssist ネイティブ通知)
        if clean_path in ('/api/notify', '/api/notification'):
            title = req_data.get('title', 'SmartHome')
            message = req_data.get('message') or req_data.get('body', '')
            priority = req_data.get('priority', 'high')
            actions = req_data.get('actions', [])
            notif_id = req_data.get('id')
            progress = req_data.get('progress')
            ongoing = req_data.get('ongoing', False)
            auto_cancel = req_data.get('auto_cancel', not ongoing)
            notif = push_service.push_notification(
                title=title,
                body=message,
                priority=priority,
                actions=actions,
                notif_id=notif_id,
                progress=progress,
                ongoing=ongoing,
                auto_cancel=auto_cancel
            )
            return self.send_json_response({"status": "success", "notification": notif})

        # 1. 家電操作 API

        if clean_path == '/api/light':
            res = execute_light_command(req_data.get('action', 'toggle'))
            return self.send_json_response(res)

        if clean_path == '/api/ac':
            res = execute_ac_command(req_data.get('mode', 'cool'), req_data.get('temp', 26), req_data.get('fan_mode', 'auto'))
            return self.send_json_response(res)

        if clean_path == '/api/heater':
            res = execute_heater_command(
                req_data.get('action', 'toggle'),
                req_data.get('count', 1),
                req_data.get('temp'),
                req_data.get('eco')
            )
            return self.send_json_response(res)

        if clean_path == '/api/cleaner':
            res = execute_cleaner_command(req_data.get('action', 'start'), req_data.get('speed'))
            return self.send_json_response(res)

        if clean_path == '/api/usb':
            action = req_data.get('action')
            if action == 'on':
                power = usb_service.set_usb_power(True)
            elif action == 'off':
                power = usb_service.set_usb_power(False)
            elif action == 'toggle':
                power = usb_service.toggle_usb_power()
            elif 'power' in req_data:
                power = usb_service.set_usb_power(bool(req_data['power']))
            else:
                power = usb_service.toggle_usb_power()
            return self.send_json_response({"status": "success", "power": power, "state": state_manager.load_state()})

        if clean_path in ('/api/pc', '/api/pc/boot', '/api/pc/shutdown', '/api/pc/os'):
            action = req_data.get('action')
            target_os = req_data.get('target_os') or req_data.get('os')
            if clean_path == '/api/pc/os' or action in ('set_os', 'select_os'):
                res = pc_service.set_target_os(target_os or 'Windows')
            elif clean_path == '/api/pc/boot' or action in ('boot', 'on', 'start'):
                res = pc_service.boot_pc()
            elif clean_path == '/api/pc/shutdown' or action in ('shutdown', 'off', 'stop'):
                res = pc_service.shutdown_pc()
            else:
                res = pc_service.toggle_pc()
            return self.send_json_response(res)

        # 2. アシスタント自然言語 API
        if clean_path == '/api/assistant':
            prompt = req_data.get('prompt', '')
            result = assistant_engine.parse_and_execute(prompt, dispatch_internal_api)
            result['state'] = state_manager.load_state()
            return self.send_json_response(result)

        # 3. シーン & オートメーション API
        if clean_path == '/api/scenes/execute':
            scene_id = req_data.get('id')
            res = flow_engine.execute_scene(scene_id, send_api_fn=dispatch_internal_api)
            res['state'] = state_manager.load_state()
            return self.send_json_response(res)

        if clean_path == '/api/automations/toggle':
            auto_id = req_data.get('id')
            res = automation_service.toggle_automation(auto_id)
            if res:
                return self.send_json_response({"status": "success", "automation": res})
            return self.send_json_response({"status": "error", "message": "Automation not found"}, status=HTTPStatus.NOT_FOUND)

        if clean_path == '/api/automations/execute':
            auto_id = req_data.get('id')
            ok = automation_service.execute_automation(auto_id)
            return self.send_json_response({"status": "success" if ok else "error"})

        # 4. 通知テスト & 互換性 API (WebPushは廃止、NovaAssistへ送信)
        if clean_path == '/api/push/subscribe':
            return self.send_json_response({"status": "disabled", "message": "WebPush is disabled in favor of NovaAssist native app."})

        if clean_path == '/api/push/test':
            try:
                notif = push_service.send_away_device_warning()
                if notif:
                    return self.send_json_response({"status": "success", "message": "Notification sent to NovaAssist", "notification": notif})
                else:
                    return self.send_json_response({"status": "skipped", "message": "No active devices, notification skipped"})
            except Exception as e:
                return self.send_json_response({"status": "error", "error": str(e)})


        # 5. 状態直接更新 API
        if clean_path == '/api/state':
            saved_state = state_manager.save_state(req_data)
            return self.send_json_response({"status": "success", "state": saved_state})

        return self.send_json_response({"status": "error", "message": "Endpoint not found"}, status=HTTPStatus.NOT_FOUND)

    def translate_path(self, path):
        if path.startswith('/dashboard'):
            path = path[len('/dashboard'):] or '/'
        return super().translate_path(path)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def send_head(self):
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            parts = urllib.parse.urlsplit(self.path)
            if not parts.path.endswith('/'):
                self.send_response(HTTPStatus.MOVED_PERMANENTLY)
                new_parts = (parts[0], parts[1], parts[2] + '/', parts[3], parts[4])
                self.send_header("Location", urllib.parse.urlunsplit(new_parts))
                self.send_header("Content-Length", "0")
                self.end_headers()
                return None
            for index in ("index.html", "index.htm"):
                index_path = os.path.join(path, index)
                if os.path.exists(index_path):
                    path = index_path
                    break
            else:
                return self.list_directory(path)

        ctype = self.guess_type(path)
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None

        try:
            fs = os.fstat(f.fileno())
            if path.endswith('.html'):
                content = f.read()
                f.close()
                if b'</body>' in content:
                    content = content.replace(b'</body>', LIVE_RELOAD_SCRIPT)
                else:
                    content += LIVE_RELOAD_SCRIPT
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-type", ctype)
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
                self.end_headers()
                return io.BytesIO(content)

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", ctype)
            self.send_header("Content-Length", str(fs[6]))
            self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
            self.end_headers()
            return f
        except Exception:
            f.close()
            raise

    def copyfile(self, source, outputfile):
        super().copyfile(source, outputfile)

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    presence_service.start_presence_service()
    tile_service.start_tile_service()
    automation_service.start_automation_service()
    watcher_thread = threading.Thread(target=file_watcher, daemon=True)
    watcher_thread.start()

    server = ThreadingHTTPServer(('0.0.0.0', PORT), LiveReloadHandler)
    server.daemon_threads = True

    print(f"🚀 Live Reload HTTP サーバーが起動しました (Port: {PORT})")
    print(f"  - ローカル:     http://localhost:{PORT}")
    print(f"  - Tailscale Funnel パス (/dashboard) 受信準備完了")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを停止しました。")
        server.server_close()
