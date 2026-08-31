#!/usr/bin/env python3
"""
Lightweight Live-Reload HTTP Server for Tailscale Serve / Funnel Proxy
Supports serving from root (/) and subpaths (/dashboard/).
"""

import os
import sys
import time
import socket
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import threading

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

clients = []
clients_lock = threading.Lock()
last_mtime = 0

def get_latest_mtime():
    max_m = 0
    for root, _, files in os.walk(DIRECTORY):
        for f in files:
            if f.endswith(('.html', '.css', '.js', '.png', '.jpg', '.svg')):
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
    // Determine the SSE path based on current path
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

import json
import switchbot_client
import eufy_client
import presence_service
import tile_service
import automation_service
import weather_service
import assistant_engine

STATE_FILE = os.path.join(DIRECTORY, 'state.json')

DEFAULT_STATE = {
    "acMode": "cool",
    "acTemp": 26,
    "acFan": "auto",
    "heaterMode": "off",
    "heaterTemp": 24,
    "heaterEco": False,
    "heaterPower": 2,
    "lightOn": False,
    "lightFull": False,
    "lightNight": False,
    "cleanerStatus": "charging",
    "cleanerPlay": False
}

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return {**DEFAULT_STATE, **json.load(f)}
        except Exception:
            pass
    return DEFAULT_STATE.copy()

def save_state(state):
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[State Save Error] {e}")

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

        if clean_path == '/api/state':
            state = load_state()
            return self.send_json_response({"status": "success", "state": state})

        if clean_path == '/api/weather':
            data = weather_service.get_weather_data()
            return self.send_json_response({"status": "success", "weather": data})

        if clean_path == '/api/presence':
            data = presence_service.get_presence_status()
            return self.send_json_response({"status": "success", "presence": data})

        if clean_path == '/api/tile':
            data = tile_service.get_tile_status()
            return self.send_json_response({"status": "success", "tile": data})

        if clean_path == '/api/automations':
            data = automation_service.load_automations()
            return self.send_json_response({"status": "success", "automations": data})

        if clean_path == '/api/cleaner/status':
            try:
                client = eufy_client.EufyG30Client()
                res = client.get_status()
                if res.get("success"):
                    current_state = load_state()
                    # status: Running, Charging, standby, Sleeping, Recharge, completed
                    current_state['cleanerStatus'] = res.get('status', 'standby').lower()
                    current_state['cleanerPlay'] = res.get('play', False)
                    save_state(current_state)
                return self.send_json_response(res)
            except Exception as e:
                return self.send_json_response({"success": False, "error": str(e)})

        # /dashboard へのリクエストを / にマップして配信
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

        if clean_path == '/api/ac':
            mode = req_data.get('mode', 'cool')
            temp = int(req_data.get('temp', 26))
            fan_mode = req_data.get('fan_mode', 'auto')

            # 状態を保存
            current_state = load_state()
            current_state['acMode'] = mode
            current_state['acTemp'] = temp
            current_state['acFan'] = fan_mode
            save_state(current_state)

            # SwitchBot API へ送信 (別スレッドで非同期送信して高速応答)
            def send_bg():
                try:
                    switchbot_client.control_ac(mode, temp, fan_mode)
                except Exception as e:
                    print(f"[AC Control Error] {e}")

            threading.Thread(target=send_bg, daemon=True).start()

        if clean_path == '/api/light':
            action = req_data.get('action', 'toggle')
            current_state = load_state()

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
                current_state['lightOn'] = not current_state['lightOn']
                action = 'turnOn' if current_state['lightOn'] else 'turnOff'
                if not current_state['lightOn']:
                    current_state['lightFull'] = False
                    current_state['lightNight'] = False

            save_state(current_state)

            def send_light_bg():
                try:
                    switchbot_client.control_light(action)
                except Exception as e:
                    print(f"[Light Control Error] {e}")

            threading.Thread(target=send_light_bg, daemon=True).start()

            return self.send_json_response({
                "status": "success",
                "message": f"Light command dispatched ({action})",
                "state": current_state
            })

        if clean_path == '/api/heater':
            action = req_data.get('action', 'toggle')
            count = max(1, min(10, int(req_data.get('count', 1))))
            current_state = load_state()

            if action in ('on', 'turnOn', 'heat'):
                current_state['heaterMode'] = 'heat'
            elif action in ('off', 'turnOff'):
                current_state['heaterMode'] = 'off'
            elif action == 'toggle':
                current_state['heaterMode'] = 'off' if current_state['heaterMode'] == 'heat' else 'heat'
                action = 'turnOn' if current_state['heaterMode'] == 'heat' else 'turnOff'
            elif action in ('eco', 'エコ'):
                current_state['heaterEco'] = req_data.get('eco', not current_state.get('heaterEco', False))
            elif action in ('plus', 'minus'):
                current_temp = current_state.get('heaterTemp', 22)
                if action == 'plus':
                    current_state['heaterTemp'] = min(28, current_temp + count)
                else:
                    current_state['heaterTemp'] = max(22, current_temp - count)
                if 'temp' in req_data:
                    current_state['heaterTemp'] = int(req_data['temp'])

            save_state(current_state)

            def send_heater_bg():
                try:
                    for i in range(count):
                        switchbot_client.control_heater(action)
                        if i < count - 1:
                            time.sleep(0.5)
                except Exception as e:
                    print(f"[Heater Control Error] {e}")

            threading.Thread(target=send_heater_bg, daemon=True).start()

            return self.send_json_response({
                "status": "success",
                "message": f"Heater command dispatched ({action}, count={count})",
                "state": current_state
            })

        if clean_path == '/api/cleaner':
            action = req_data.get('action', 'start')
            speed = req_data.get('speed')
            current_state = load_state()

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

            save_state(current_state)

            def send_cleaner_bg():
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

            threading.Thread(target=send_cleaner_bg, daemon=True).start()

            return self.send_json_response({
                "status": "success",
                "message": f"Cleaner command dispatched ({action})",
                "state": current_state
            })

        if clean_path == '/api/assistant':
            prompt = req_data.get('prompt', '')

            def internal_api_caller(endpoint, payload):
                if endpoint == '/api/light':
                    action = payload.get('action', 'toggle')
                    current_st = load_state()
                    if action in ('on', 'turnOn', 'full', 'night'):
                        current_st['lightOn'] = True
                        if action == 'full':
                            current_st['lightFull'] = True
                            current_st['lightNight'] = False
                        elif action == 'night':
                            current_st['lightNight'] = True
                            current_st['lightFull'] = False
                    elif action in ('off', 'turnOff'):
                        current_st['lightOn'] = False
                        current_st['lightFull'] = False
                        current_st['lightNight'] = False
                    elif action == 'toggle':
                        current_st['lightOn'] = not current_st['lightOn']
                        action = 'turnOn' if current_st['lightOn'] else 'turnOff'
                    save_state(current_st)
                    threading.Thread(target=lambda: switchbot_client.control_light(action), daemon=True).start()

                elif endpoint == '/api/ac':
                    mode = payload.get('mode', 'cool')
                    temp = int(payload.get('temp', 26))
                    fan = payload.get('fan_mode', 'auto')
                    current_st = load_state()
                    current_st['acMode'] = mode
                    current_st['acTemp'] = temp
                    current_st['acFan'] = fan
                    save_state(current_st)
                    threading.Thread(target=lambda: switchbot_client.control_ac(mode, temp, fan), daemon=True).start()

                elif endpoint == '/api/heater':
                    action = payload.get('action', 'heat')
                    temp = payload.get('temp')
                    current_st = load_state()
                    if action in ('on', 'turnOn', 'heat'):
                        current_st['heaterMode'] = 'heat'
                    elif action in ('off', 'turnOff'):
                        current_st['heaterMode'] = 'off'
                    if temp:
                        current_st['heaterTemp'] = int(temp)
                    save_state(current_st)
                    threading.Thread(target=lambda: switchbot_client.control_heater(action), daemon=True).start()

                elif endpoint == '/api/cleaner':
                    action = payload.get('action', 'start')
                    current_st = load_state()
                    if action in ('start', 'play', 'resume'):
                        current_st['cleanerStatus'] = 'running'
                        current_st['cleanerPlay'] = True
                    elif action in ('pause',):
                        current_st['cleanerStatus'] = 'standby'
                        current_st['cleanerPlay'] = False
                    elif action in ('stop', 'dock', 'home', 'return'):
                        current_st['cleanerStatus'] = 'recharge'
                        current_st['cleanerPlay'] = False
                    save_state(current_st)
                    def run_cleaner():
                        try:
                            c = eufy_client.EufyG30Client()
                            if action in ('start', 'play', 'resume'): c.play()
                            elif action in ('pause',): c.pause()
                            elif action in ('stop', 'dock', 'home', 'return'): c.return_to_dock()
                            elif action in ('find', 'find_me', 'beep'): c.find_robot()
                        except Exception as ce:
                            print(f"[Cleaner Assistant Error] {ce}")
                    threading.Thread(target=run_cleaner, daemon=True).start()

            result = assistant_engine.parse_and_execute(prompt, internal_api_caller)
            result['state'] = load_state()
            return self.send_json_response(result)

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

        if clean_path == '/api/state':
            current_state = load_state()
            current_state.update(req_data)
            save_state(current_state)
            return self.send_json_response({"status": "success", "state": current_state})

        return self.send_json_response({"status": "error", "message": "Endpoint not found"}, status=HTTPStatus.NOT_FOUND)

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
    print(f"  - Tailscale IP: http://100.100.1.1:{PORT}")
    print(f"  - Tailscale Funnel パス (/dashboard) 受信準備完了")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを停止しました。")
        server.server_close()
