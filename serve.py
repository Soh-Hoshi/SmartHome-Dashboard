#!/usr/bin/env python3
"""
Lightweight Live-Reload HTTP Server for SmartHome Dashboard
Supports serving from root (/) and subpaths (/dashboard/) over Tailscale HTTPS.
"""

import os
import sys
import time
import json
import socket
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
            if f.endswith(('.html', '.css', '.js', '.png', '.jpg', '.svg', '.json')) and not f.endswith(('weather_cache.json', 'server.log')):
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

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        clean_path = self.path
        if clean_path.startswith('/dashboard'):
            clean_path = clean_path[len('/dashboard'):] or '/'

        # LiveReload SSE
        if clean_path == '/__livereload__':
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            queue = []
            with clients_lock:
                clients.append(queue)
            try:
                self.wfile.write(b"data: connected\n\n")
                self.wfile.flush()
                while True:
                    time.sleep(0.2)
                    if queue:
                        msg = queue.pop(0)
                        self.wfile.write(f"data: {msg}\n\n".encode('utf-8'))
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                with clients_lock:
                    if queue in clients:
                        clients.remove(queue)
            return

        # GET API ルーティング
        get_routes = {
            '/api/state': lambda: {"status": "success", "state": state_manager.load_state()},
            '/api/weather': lambda: {"status": "success", "weather": weather_service.get_weather_data()},
            '/api/presence': lambda: {"status": "success", "presence": presence_service.get_presence_status()},
            '/api/tile': lambda: {"status": "success", "tile": tile_service.get_tile_status()},
            '/api/automations': lambda: {"status": "success", "automations": automation_service.load_automations()},
            '/api/scenes': lambda: {"status": "success", "scenes": flow_engine.load_scenes()},
        }

        if clean_path in get_routes:
            try:
                return self.send_json_response(get_routes[clean_path]())
            except Exception as e:
                return self.send_json_response({"status": "error", "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        if clean_path == '/api/push/vapid-key':
            try:
                import push_service
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
        clean_path = self.path
        if clean_path.startswith('/dashboard'):
            clean_path = clean_path[len('/dashboard'):] or '/'

        content_len = int(self.headers.get('Content-Length', 0))
        post_body = self.rfile.read(content_len) if content_len > 0 else b'{}'
        try:
            req_data = json.loads(post_body.decode('utf-8'))
        except Exception:
            req_data = {}

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

        # 4. WebPush API
        if clean_path == '/api/push/subscribe':
            try:
                import push_service
                sub_data = req_data.get('subscription', req_data)
                ok = push_service.save_subscription(sub_data)
                return self.send_json_response({"status": "success" if ok else "error"})
            except Exception as e:
                return self.send_json_response({"status": "error", "error": str(e)})

        if clean_path == '/api/push/test':
            try:
                import push_service
                count = push_service.send_away_device_warning("リビング照明・エアコン（冷房）")
                return self.send_json_response({"status": "success", "subscribers": count})
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

    def copyfile(self, source, outputfile):
        if hasattr(source, 'name') and source.name.endswith('.html'):
            content = source.read()
            if b'</body>' in content:
                content = content.replace(b'</body>', LIVE_RELOAD_SCRIPT)
            else:
                content += LIVE_RELOAD_SCRIPT
            outputfile.write(content)
        else:
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

    print(f"🚀 Live Reload HTTP サーバーが起動しました (Port: {PORT})")
    print(f"  - ローカル:     http://localhost:{PORT}")
    print(f"  - Tailscale Funnel パス (/dashboard) 受信準備完了")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを停止しました。")
        server.server_close()
