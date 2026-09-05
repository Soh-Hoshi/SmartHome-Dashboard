#!/usr/bin/env python3
"""
Desktop PC Service (Windows & Bazzite Dual-Boot Control)
Handles Wake-on-LAN (Boot), presence detection, and remote shutdown via SSH.
Supports optimistic transient states ('booting', 'shutting_down') with automatic background monitoring.
"""

import socket
import subprocess
import threading
import time
import state_manager

PC_DEFAULT_IP = "192.168.0.51"
PC_IP = PC_DEFAULT_IP
PC_MAC = "a8:a1:59:60:6f:c0"
PC_PORT = 22
PC_BROADCAST = "192.168.0.255"
USERS = ["user", "soh"]
PASSWORD = "Tamago1341"

BOOT_TIMEOUT = 90.0        # 起動待機最大秒数
SHUTDOWN_TIMEOUT = 60.0    # 終了待機最大秒数

_lock = threading.Lock()
_cached_status = None
_last_check = 0
_last_scan_time = 0

# 楽観的トランジェント状態 ('booting' | 'shutting_down' | None)
_transient_state = None
_transient_timestamp = 0.0

def resolve_pc_ip(force_scan=False):
    """
    MACアドレス (a8:a1:59:60:6f:c0) から現在のPCのIPアドレスを動的に解決。
    BazziteがDHCPで別IPを取得した場合でも自動追跡。
    """
    global PC_IP, _last_scan_time
    clean_target = PC_MAC.lower().replace("-", ":")

    def _check_tables():
        # 1. /proc/net/arp
        try:
            with open("/proc/net/arp", "r") as f:
                for line in f.readlines()[1:]:
                    parts = line.split()
                    if len(parts) >= 4:
                        ip, flags, mac = parts[0], parts[2], parts[3].lower()
                        if mac == clean_target and flags != "0x0":
                            return ip
        except Exception:
            pass

        # 2. ip neigh
        try:
            res = subprocess.run(["ip", "neigh"], capture_output=True, text=True, check=False)
            for line in res.stdout.splitlines():
                if clean_target in line.lower():
                    parts = line.split()
                    if "FAILED" not in line and len(parts) > 0:
                        return parts[0]
        except Exception:
            pass
        return None

    found_ip = _check_tables()
    if found_ip:
        if PC_IP != found_ip:
            print(f"[PC Resolver] PC IP updated from {PC_IP} to {found_ip} (MAC: {PC_MAC})")
            PC_IP = found_ip
        return found_ip

    now = time.time()
    if force_scan or (now - _last_scan_time > 30.0):
        _last_scan_time = now
        try:
            subprocess.run(["nmap", "-sn", "192.168.0.0/24"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            found_ip = _check_tables()
            if found_ip:
                if PC_IP != found_ip:
                    print(f"[PC Resolver] PC IP discovered: {found_ip} (MAC: {PC_MAC})")
                    PC_IP = found_ip
                return found_ip
        except Exception as e:
            print(f"[PC Resolver] Subnet scan error: {e}")

    return PC_IP

def send_wol(mac_address: str = PC_MAC, broadcast_ip: str = PC_BROADCAST):
    """
    Wake-on-LAN Magic Packet をマルチパス方式で強力送信
    1. レイヤー2 RAW イーサネット (etherwake -i enp3s0)
    2. システム wakeonlan コマンド (サブネット / グローバル / ユニキャスト)
    3. Python UDP ソケット (ポート 9, 7, 0 / バースト送信)
    """
    clean_mac = mac_address.replace(":", "").replace("-", "").strip()
    if len(clean_mac) != 12:
        raise ValueError(f"Invalid MAC address: {mac_address}")
    formatted_mac = ":".join(clean_mac[i:i+2] for i in range(0, 12, 2))

    # 1. レイヤー2 RAW 送信 (etherwake) - OS/IPスタックを迂回する物理フレーム送信
    try:
        subprocess.run(["etherwake", "-i", "enp3s0", formatted_mac], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[WoL etherwake Error] {e}")

    # 2. システム wakeonlan コマンド
    try:
        subprocess.run(["wakeonlan", "-i", broadcast_ip, "-p", "9", formatted_mac], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["wakeonlan", "-i", "255.255.255.255", "-p", "9", formatted_mac], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["wakeonlan", "-i", PC_IP, "-p", "9", formatted_mac], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[WoL wakeonlan Error] {e}")

    # 3. Python UDP ソケット バースト送信 (3回リピート)
    mac_bytes = bytes.fromhex(clean_mac)
    magic_packet = b'\xff' * 6 + mac_bytes * 16

    targets = [
        (broadcast_ip, 9),
        (broadcast_ip, 7),
        ("255.255.255.255", 9),
        ("255.255.255.255", 7),
        (PC_IP, 9),
        (PC_IP, 7),
    ]

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            try:
                s.setsockopt(socket.SOL_SOCKET, 25, b"enp3s0\0")
            except Exception:
                pass
            for _ in range(3):
                for target in targets:
                    try:
                        s.sendto(magic_packet, target)
                    except Exception:
                        pass
                time.sleep(0.05)
    except Exception as e:
        print(f"[WoL socket Error] {e}")

    print(f"[WoL Sent] Multi-path magic packet dispatched to {formatted_mac} (broadcast: {broadcast_ip}, unicast: {PC_IP})")

def detect_os_from_banner():
    """SSHバナーおよび稼働ポートからOS (Windows / Bazzite) を判別"""
    current_ip = resolve_pc_ip()

    # 1. SSH バナー取得
    try:
        s = socket.socket()
        s.settimeout(1.0)
        s.connect((current_ip, PC_PORT))
        banner = s.recv(1024).decode('utf-8', errors='ignore')
        s.close()
        if "OpenSSH_for_Windows" in banner:
            return "Windows"
        elif "SSH-" in banner:
            return "Bazzite"
    except Exception:
        pass

    # 2. ポートベース推定 (Windows特有ポート)
    for p in [135, 445, 5985]:
        try:
            s = socket.socket()
            s.settimeout(0.3)
            if s.connect_ex((current_ip, p)) == 0:
                s.close()
                return "Windows"
            s.close()
        except Exception:
            pass

    # 3. Steam ポート (27036) または Linux / Bazzite 推定
    try:
        s = socket.socket()
        s.settimeout(0.3)
        if s.connect_ex((current_ip, 27036)) == 0:
            s.close()
            return "Bazzite"
        s.close()
    except Exception:
        pass

    # オンラインであればデフォルトで Bazzite と判定（Windows特有ポートが開いていないため）
    return "Bazzite"

def is_pc_online(force_scan=False):
    """ポート疎通またはPingでPCの稼働を確認"""
    current_ip = resolve_pc_ip(force_scan=force_scan)

    # 1. 既知ポート疎通プローブ (SSH, Windows RPC, SMB, WinRM, Steam Streaming)
    probe_ports = [PC_PORT, 135, 445, 5985, 27036]
    for p in probe_ports:
        try:
            s = socket.socket()
            s.settimeout(0.3)
            res = s.connect_ex((current_ip, p))
            s.close()
            if res == 0:
                return True
        except Exception:
            pass

    # 2. ICMP Ping
    try:
        r = subprocess.run(["ping", "-c", "1", "-W", "1", current_ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode == 0:
            return True
    except Exception:
        pass

    # 3. ARPステータスチェック
    try:
        clean_target = PC_MAC.lower().replace("-", ":")
        res = subprocess.run(["ip", "neigh"], capture_output=True, text=True, check=False)
        for line in res.stdout.splitlines():
            if clean_target in line.lower() and any(st in line for st in ["REACHABLE", "DELAY", "PROBE"]):
                return True
    except Exception:
        pass

    return False

def _monitor_boot():
    """バックグラウンドで起動完了を監視し、完全起動時にステートを確定"""
    global _transient_state, _cached_status
    start = time.time()
    while time.time() - start < BOOT_TIMEOUT:
        time.sleep(2.0)
        with _lock:
            if _transient_state != 'booting':
                return

        # 起動監視中は能動的にサブネット探索も含めてチェック
        if is_pc_online(force_scan=True):
            os_name = detect_os_from_banner()
            with _lock:
                _transient_state = None
                _cached_status = {
                    "online": True,
                    "booting": False,
                    "shutting_down": False,
                    "os": os_name,
                    "ip": PC_IP
                }
                try:
                    state_manager.save_state({"pcOnline": True, "pcOs": os_name})
                except Exception:
                    pass
            print(f"[PC Monitor] PC booted: {os_name} at {PC_IP}")
            return

    # タイムアウト
    with _lock:
        if _transient_state == 'booting':
            _transient_state = None
            _cached_status = {
                "online": False,
                "booting": False,
                "shutting_down": False,
                "os": "オフライン",
                "ip": PC_IP
            }
            try:
                state_manager.save_state({"pcOnline": False, "pcOs": "オフライン"})
            except Exception:
                pass
            print("[PC Monitor] PC boot timed out.")

def _monitor_shutdown():
    """バックグラウンドで電源オフを監視し、電源切断時にステートを確定"""
    global _transient_state, _cached_status
    start = time.time()
    while time.time() - start < SHUTDOWN_TIMEOUT:
        time.sleep(2.0)
        with _lock:
            if _transient_state != 'shutting_down':
                return
        if not is_pc_online():
            with _lock:
                _transient_state = None
                _cached_status = {
                    "online": False,
                    "booting": False,
                    "shutting_down": False,
                    "os": "オフライン",
                    "ip": PC_IP
                }
                try:
                    state_manager.save_state({"pcOnline": False, "pcOs": "オフライン"})
                except Exception:
                    pass
            print("[PC Monitor] PC shutdown confirmed.")
            return

    # タイムアウト
    with _lock:
        if _transient_state == 'shutting_down':
            _transient_state = None

def get_pc_status(force_refresh=False):
    global _cached_status, _last_check, _transient_state, _transient_timestamp
    now = time.time()
    with _lock:
        # 1. 起動中（booting）トランジェント期間
        if _transient_state == 'booting':
            if now - _transient_timestamp < BOOT_TIMEOUT:
                if is_pc_online():
                    os_name = detect_os_from_banner()
                    _transient_state = None
                    _cached_status = {
                        "online": True,
                        "booting": False,
                        "shutting_down": False,
                        "os": os_name,
                        "ip": PC_IP
                    }
                    try:
                        state_manager.save_state({"pcOnline": True, "pcOs": os_name})
                    except Exception:
                        pass
                    return _cached_status

                # まだ起動中 (楽観的ON)
                return {
                    "online": True,
                    "booting": True,
                    "shutting_down": False,
                    "os": "起動中...",
                    "ip": PC_IP
                }
            else:
                _transient_state = None

        # 2. 終了中（shutting_down）トランジェント期間
        elif _transient_state == 'shutting_down':
            if now - _transient_timestamp < SHUTDOWN_TIMEOUT:
                if not is_pc_online():
                    _transient_state = None
                    _cached_status = {
                        "online": False,
                        "booting": False,
                        "shutting_down": False,
                        "os": "オフライン",
                        "ip": PC_IP
                    }
                    try:
                        state_manager.save_state({"pcOnline": False, "pcOs": "オフライン"})
                    except Exception:
                        pass
                    return _cached_status

                # まだ終了中 (楽観的OFF)
                return {
                    "online": False,
                    "booting": False,
                    "shutting_down": True,
                    "os": "終了中...",
                    "ip": PC_IP
                }
            else:
                _transient_state = None

        if not force_refresh and _cached_status is not None and (now - _last_check < 3.0):
            return _cached_status

        online = is_pc_online(force_scan=False)
        os_name = detect_os_from_banner() if online else "オフライン"

        _cached_status = {
            "online": online,
            "booting": False,
            "shutting_down": False,
            "os": os_name,
            "ip": PC_IP
        }
        _last_check = now
        try:
            state_manager.save_state({"pcOnline": online, "pcOs": os_name})
        except Exception:
            pass
        return _cached_status

def boot_pc():
    """Wake-on-LAN を送信し、楽観的起動ステートを開始"""
    global _transient_state, _transient_timestamp, _cached_status
    st = get_pc_status(force_refresh=True)
    if st["online"] and not st.get("booting") and not st.get("shutting_down"):
        return {
            "status": "warning",
            "message": f"PCは既に起動しています ({st.get('os')})。",
            "online": True,
            "os": st.get("os")
        }

    try:
        send_wol()
    except Exception as e:
        return {
            "status": "error",
            "message": f"WoLの送信に失敗しました: {e}"
        }

    with _lock:
        _transient_state = 'booting'
        _transient_timestamp = time.time()
        _cached_status = {
            "online": True,
            "booting": True,
            "shutting_down": False,
            "os": "起動中...",
            "ip": PC_IP
        }
        try:
            state_manager.save_state({"pcOnline": True, "pcOs": "起動中..."})
        except Exception:
            pass

    threading.Thread(target=_monitor_boot, daemon=True).start()

    return {
        "status": "success",
        "message": "起動シグナル(WoL)を送信しました。起動中...",
        "online": True,
        "booting": True,
        "os": "起動中..."
    }

def shutdown_pc():
    """OSを自動判別して適切なシャットダウンコマンドをSSH送信"""
    global _transient_state, _transient_timestamp, _cached_status

    st = get_pc_status(force_refresh=True)
    if not st["online"] and not st.get("booting"):
        return {
            "status": "warning",
            "message": "PCはすでにオフラインです。",
            "online": False,
            "os": "オフライン"
        }

    os_type = st.get("os", "Windows")
    if os_type == "Windows":
        remote_cmd = 'shutdown.exe /s /t 0'
    else:
        remote_cmd = f'systemctl poweroff || sudo poweroff || echo {PASSWORD} | sudo -S systemctl poweroff || shutdown -h now'

    current_ip = resolve_pc_ip()
    last_err = None
    sent = False
    for u in USERS:
        cmd_key = [
            "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=3", f"{u}@{current_ip}", remote_cmd
        ]
        res = subprocess.run(cmd_key, capture_output=True, text=True)
        if res.returncode == 0:
            sent = True
            break

        cmd_pass = [
            "sshpass", "-p", PASSWORD,
            "ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=3",
            f"{u}@{current_ip}", remote_cmd
        ]
        res = subprocess.run(cmd_pass, capture_output=True, text=True)
        if res.returncode == 0:
            sent = True
            break
        else:
            last_err = res.stderr or res.stdout

    if sent:
        with _lock:
            _transient_state = 'shutting_down'
            _transient_timestamp = time.time()
            _cached_status = {
                "online": False,
                "booting": False,
                "shutting_down": True,
                "os": "終了中...",
                "ip": current_ip
            }
            try:
                state_manager.save_state({"pcOnline": False, "pcOs": "終了中..."})
            except Exception:
                pass

        threading.Thread(target=_monitor_shutdown, daemon=True).start()

        return {
            "status": "success",
            "message": f"{os_type} にシャットダウンを指示しました。",
            "online": False,
            "shutting_down": True,
            "os": "終了中..."
        }

    return {
        "status": "error",
        "message": f"シャットダウンの送信に失敗しました: {last_err}",
        "os": os_type
    }

def toggle_pc():
    """トグル動作: オンならシャットダウン、オフならWoL起動"""
    st = get_pc_status()
    if st.get("booting"):
        return {"status": "info", "message": "現在起動処理中です...", **st}
    if st.get("shutting_down"):
        return {"status": "info", "message": "現在終了処理中です...", **st}

    if st.get("online"):
        return shutdown_pc()
    else:
        return boot_pc()

if __name__ == '__main__':
    print("PC Status:", get_pc_status(force_refresh=True))

