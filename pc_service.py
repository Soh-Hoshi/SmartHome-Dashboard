#!/usr/bin/env python3
"""
Desktop PC Service (Windows & Bazzite Dual-Boot Control)
Handles presence detection and remote shutdown via SSH.
"""

import socket
import subprocess
import threading
import time
import state_manager

PC_IP = "192.168.0.51"
PC_PORT = 22
USERS = ["user", "soh"]
PASSWORD = "Tamago1341"

_lock = threading.Lock()
_cached_status = None
_last_check = 0

def detect_os_from_banner():
    """SSHバナーから稼働中OS (Windows / Bazzite) を判別"""
    try:
        s = socket.socket()
        s.settimeout(1.0)
        s.connect((PC_IP, PC_PORT))
        banner = s.recv(1024).decode('utf-8', errors='ignore')
        s.close()
        if "OpenSSH_for_Windows" in banner:
            return "Windows"
        elif "SSH-" in banner:
            return "Bazzite"
        return "Unknown"
    except Exception:
        return "Unknown"

def is_pc_online():
    """ポート22疎通またはPingでPCの稼働を確認"""
    try:
        s = socket.socket()
        s.settimeout(0.5)
        res = s.connect_ex((PC_IP, PC_PORT))
        s.close()
        if res == 0:
            return True
    except Exception:
        pass

    try:
        r = subprocess.run(["ping", "-c", "1", "-W", "1", PC_IP], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return r.returncode == 0
    except Exception:
        return False

def get_pc_status(force_refresh=False):
    global _cached_status, _last_check
    now = time.time()
    with _lock:
        if not force_refresh and _cached_status is not None and (now - _last_check < 3.0):
            return _cached_status

        online = is_pc_online()
        os_name = detect_os_from_banner() if online else "オフライン"

        _cached_status = {
            "online": online,
            "os": os_name,
            "ip": PC_IP
        }
        _last_check = now
        try:
            state_manager.save_state({"pcOnline": online, "pcOs": os_name})
        except Exception:
            pass
        return _cached_status

def shutdown_pc():
    """OSを自動判別して適切なシャットダウンコマンドをSSH送信"""
    st = get_pc_status(force_refresh=True)
    if not st["online"]:
        return {
            "status": "warning",
            "message": "PCはすでにオフラインです。",
            "os": "オフライン"
        }

    os_type = st["os"]
    if os_type == "Windows":
        # Windowsシャットダウンコマンド
        remote_cmd = 'shutdown.exe /s /t 0'
    else:
        # Bazzite (Linux) シャットダウンコマンド (ポリシーキット、sudo、パスワード付きsudo)
        remote_cmd = f'systemctl poweroff || sudo poweroff || echo {PASSWORD} | sudo -S systemctl poweroff || shutdown -h now'

    last_err = None
    for u in USERS:
        # 1. 鍵認証を試行
        cmd_key = [
            "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=3", f"{u}@{PC_IP}", remote_cmd
        ]
        res = subprocess.run(cmd_key, capture_output=True, text=True)
        if res.returncode == 0:
            try:
                state_manager.save_state({"pcOnline": False, "pcOs": "シャットダウン中..."})
            except Exception:
                pass
            return {
                "status": "success",
                "message": f"{os_type} にシャットダウンを指示しました。",
                "os": os_type,
                "user": u
            }

        # 2. sshpass によるパスワード認証を試行
        cmd_pass = [
            "sshpass", "-p", PASSWORD,
            "ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=3",
            f"{u}@{PC_IP}", remote_cmd
        ]
        res = subprocess.run(cmd_pass, capture_output=True, text=True)
        if res.returncode == 0:
            try:
                state_manager.save_state({"pcOnline": False, "pcOs": "シャットダウン中..."})
            except Exception:
                pass
            return {
                "status": "success",
                "message": f"{os_type} にシャットダウンを指示しました。",
                "os": os_type,
                "user": u
            }
        else:
            last_err = res.stderr or res.stdout

    return {
        "status": "error",
        "message": f"シャットダウンの送信に失敗しました: {last_err}",
        "os": os_type
    }

if __name__ == '__main__':
    print("PC Status:", get_pc_status(force_refresh=True))

