#!/usr/bin/env python3
"""
WebPush & Notification Service for SmartHome Dashboard
Handles VAPID key generation, subscriber management, and RFC 8291/8292 WebPush notifications.
"""

import os
import json
import time
import struct
import base64
import queue
import threading
import urllib.request
import urllib.error
from urllib.parse import urlparse

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

VAPID_FILE = "/home/soh/dashboard/vapid_keys.json"
SUBSCRIPTIONS_FILE = "/home/soh/dashboard/push_subscriptions.json"
_lock = threading.Lock()

# SSE クライアント（NovaAssist等）および通知キュー
_sse_clients = []
_sse_lock = threading.Lock()
_notif_history = []
_history_lock = threading.Lock()
MAX_HISTORY = 50

def register_sse_client():
    q = queue.Queue(maxsize=100)
    with _sse_lock:
        _sse_clients.append(q)
    return q

def unregister_sse_client(q):
    with _sse_lock:
        if q in _sse_clients:
            _sse_clients.remove(q)

def get_notifications_since(since_timestamp=0.0):
    with _history_lock:
        return [n for n in _notif_history if n.get("timestamp", 0) > since_timestamp]


def _b64_url_encode(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def _b64_url_decode(s):
    s += '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)

def get_or_create_vapid_keys():
    """VAPID キーペア（公開鍵・秘密鍵）を取得または新規生成"""
    with _lock:
        if os.path.exists(VAPID_FILE):
            try:
                with open(VAPID_FILE, 'r', encoding='utf-8') as f:
                    keys = json.load(f)
                    if 'public_key' in keys and 'private_key' in keys:
                        return keys
            except Exception as e:
                print(f"[VAPID Load Error] {e}")

        # 新規生成 (NIST P-256 / secp256r1)
        priv_key = ec.generate_private_key(ec.SECP256R1())
        pub_key = priv_key.public_key()

        priv_bytes = priv_key.private_numbers().private_value.to_bytes(32, 'big')
        pub_bytes = pub_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )

        keys = {
            "public_key": _b64_url_encode(pub_bytes),
            "private_key": _b64_url_encode(priv_bytes)
        }

        try:
            with open(VAPID_FILE, 'w', encoding='utf-8') as f:
                json.dump(keys, f, indent=2)
            print("[VAPID] New VAPID keys generated and saved.")
        except Exception as e:
            print(f"[VAPID Save Error] {e}")

        return keys

def load_subscriptions():
    """保存されたサブスクリプションリストを取得"""
    with _lock:
        if os.path.exists(SUBSCRIPTIONS_FILE):
            try:
                with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return []

def save_subscription(subscription_data):
    """PWA WebPush は廃止されたため何もしない"""
    return False

def remove_subscription(endpoint):
    """期限切れサブスクリプションを削除"""
    with _lock:
        if not os.path.exists(SUBSCRIPTIONS_FILE):
            return
        try:
            with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
                subs = json.load(f)
            filtered = [s for s in subs if s.get('endpoint') != endpoint]
            with open(SUBSCRIPTIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(filtered, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

def _encrypt_payload(payload_bytes, user_pub_b64, user_auth_b64):
    """RFC 8291 aes128gcm 暗号化"""
    p256dh = _b64_url_decode(user_pub_b64)
    auth = _b64_url_decode(user_auth_b64)

    ephemeral_priv = ec.generate_private_key(ec.SECP256R1())
    ephemeral_pub_bytes = ephemeral_priv.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )

    peer_pub = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), p256dh)
    shared_secret = ephemeral_priv.exchange(ec.ECDH(), peer_pub)

    prk = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=auth,
        info=b'WebPush: info\x00' + p256dh + ephemeral_pub_bytes
    ).derive(shared_secret)

    salt = os.urandom(16)
    cek = HKDF(
        algorithm=hashes.SHA256(),
        length=16,
        salt=salt,
        info=b'Content-Encoding: aes128gcm\x00'
    ).derive(prk)

    nonce = HKDF(
        algorithm=hashes.SHA256(),
        length=12,
        salt=salt,
        info=b'Content-Encoding: nonce\x00'
    ).derive(prk)

    padded_payload = payload_bytes + b'\x02'
    aesgcm = AESGCM(cek)
    ciphertext = aesgcm.encrypt(nonce, padded_payload, None)

    rs = 4096
    header = salt + struct.pack('>I', rs) + bytes([len(ephemeral_pub_bytes)]) + ephemeral_pub_bytes
    return header + ciphertext

def _create_vapid_auth_header(endpoint, vapid_private_b64, vapid_public_b64, sub='mailto:admin@smarthome.local'):
    """RFC 8292 VAPID JWT 認証ヘッダー作成"""
    parsed = urlparse(endpoint)
    audience = f'{parsed.scheme}://{parsed.netloc}'

    header = {'typ': 'JWT', 'alg': 'ES256'}
    claims = {
        'aud': audience,
        'exp': int(time.time()) + 12 * 3600,
        'sub': sub
    }

    hdr_b64 = _b64_url_encode(json.dumps(header))
    cls_b64 = _b64_url_encode(json.dumps(claims))
    sign_input = f'{hdr_b64}.{cls_b64}'.encode('utf-8')

    priv_num = int.from_bytes(_b64_url_decode(vapid_private_b64), 'big')
    priv_key = ec.derive_private_key(priv_num, ec.SECP256R1())

    der_sig = priv_key.sign(sign_input, ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der_sig)
    raw_sig = r.to_bytes(32, 'big') + s.to_bytes(32, 'big')

    jwt = f'{hdr_b64}.{cls_b64}.{_b64_url_encode(raw_sig)}'
    return f'vapid t={jwt}, k={vapid_public_b64}'

def send_push_to_subscriber(sub, payload_dict, vapid_keys):
    """単一サブスクライバーへ WebPush 送信"""
    endpoint = sub.get('endpoint')
    keys = sub.get('keys', {})
    p256dh = keys.get('p256dh')
    auth = keys.get('auth')

    if not endpoint or not p256dh or not auth:
        return False

    try:
        payload_bytes = json.dumps(payload_dict, ensure_ascii=False).encode('utf-8')
        body = _encrypt_payload(payload_bytes, p256dh, auth)
        auth_header = _create_vapid_auth_header(endpoint, vapid_keys['private_key'], vapid_keys['public_key'])

        req = urllib.request.Request(endpoint, data=body, method='POST')
        req.add_header('Content-Type', 'application/octet-stream')
        req.add_header('Content-Encoding', 'aes128gcm')
        req.add_header('Authorization', auth_header)
        req.add_header('TTL', '3600')
        req.add_header('Urgency', 'high')

        with urllib.request.urlopen(req, timeout=8) as res:
            if res.status in (200, 201, 202):
                return True
    except urllib.error.HTTPError as e:
        if e.code in (404, 410):
            print(f"[Push Service] Subscriber gone ({e.code}). Removing endpoint: {endpoint}")
            remove_subscription(endpoint)
        else:
            print(f"[Push Service HTTP Error] {e.code} for {endpoint}: {e.reason}")
    except Exception as e:
        print(f"[Push Service Send Error] {e}")

    return False

def broadcast_notification(title, body, actions=None, tag=None, data=None):
    """PWA WebPush は廃止（NovaAssist ネイティブアプリへの通知に一本化）"""
    return 0

def push_notification(title: str, body: str, actions=None, tag=None, data=None, priority="high",
                      notif_id=None, progress=None, ongoing=False, auto_cancel=True):
    """
    NovaAssist アプリ (SSE/Poll) へ高機能ネイティブ通知を配信
    - actions: タップで即時コマンド実行するボタン配列 (例: [{"id":"leaving", "title":"🚪 いってきます", "command":"いってきます"}])
    - reply (Direct Reply): {"id":"reply", "title":"💬 指示", "reply": True, "reply_placeholder":"Novaへ..."}
    - progress: {"current": 65, "max": 100, "indeterminate": False}
    - notif_id: 固定IDを指定するとインプレース更新（同じ通知の上書き）が可能
    """
    if not notif_id:
        notif_id = f"notif_{int(time.time() * 1000)}_{os.urandom(3).hex()}"

    notif_obj = {
        "id": notif_id,
        "title": title,
        "body": body,
        "message": body,
        "priority": priority,
        "tag": tag or "smarthome-alert",
        "timestamp": time.time(),
        "actions": actions or [],
        "data": data or {"url": "/dashboard"},
        "ongoing": ongoing,
        "auto_cancel": auto_cancel
    }
    if progress:
        notif_obj["progress"] = progress

    # 1. 履歴に追加 (ポーリング用: 既存通知の更新時は末尾に再追加して時系列順を維持)
    with _history_lock:
        existing_idx = next((i for i, n in enumerate(_notif_history) if n.get("id") == notif_id), None)
        if existing_idx is not None:
            _notif_history.pop(existing_idx)
        _notif_history.append(notif_obj)
        if len(_notif_history) > MAX_HISTORY:
            _notif_history.pop(0)

    # 2. SSE クライアント（NovaAssist等）へ即時配信
    with _sse_lock:
        for q in _sse_clients:
            try:
                q.put_nowait(notif_obj)
            except Exception:
                pass

    print(f"[Push Service] Notification dispatched to NovaAssist: id={notif_id} '{title}' - '{body}' (SSE clients: {len(_sse_clients)})")
    return notif_obj

def send_away_device_warning(active_devices_str=None):
    """
    外出時消し忘れ防止通知（電気等の稼働機器がある場合のみ送信）
    説明文・不要ボタン・アイコンを排除し、「いってきます」「novaへ指示」の2つのみ提供。
    """
    import state_manager
    st = state_manager.load_state()

    active_devices = []
    if st.get('lightOn', False):
        active_devices.append('リビング照明')
    if st.get('acMode', 'off') != 'off':
        mode_str = 'エアコン（冷房）' if st.get('acMode') == 'cool' else ('エアコン（除湿）' if st.get('acMode') == 'dry' else 'エアコン')
        active_devices.append(mode_str)
    if st.get('heaterMode', 'off') != 'off':
        active_devices.append('ヒーター')

    dev_str = active_devices_str or ('・'.join(active_devices) if active_devices else None)
    if not dev_str:
        print("[Push Service] 外出検知: 電気等の稼働機器がないため、通知を送信しませんでした。")
        return None

    title = "お出かけですか？"
    body = dev_str
    actions = [
        {
            "id": "run_leaving",
            "title": "いってきます",
            "command": "いってきます"
        },
        {
            "id": "reply_nova",
            "title": "novaへ指示",
            "reply": True,
            "reply_placeholder": "Novaに指示..."
        }
    ]
    return push_notification(
        title=title,
        body=body,
        actions=actions,
        notif_id="away-device-warning",
        tag="away-device-warning",
        data={"url": "/dashboard", "scene": "leaving"}
    )

def send_progress_notification(title: str, body: str, current: int, max_val: int = 100,
                               indeterminate: bool = False, notif_id: str = "nova_progress_bar", ongoing: bool = True):
    """
    プログレスバー付き通知を発行・更新（同一notif_idでプログレスバーが滑らかに進む）
    """
    progress = {
        "current": current,
        "max": max_val,
        "indeterminate": indeterminate
    }
    actions = [
        {"id": "dismiss", "title": "閉じる", "dismiss": True}
    ] if not ongoing else []
    return push_notification(
        title=title,
        body=body,
        notif_id=notif_id,
        progress=progress,
        ongoing=ongoing,
        auto_cancel=not ongoing,
        actions=actions
    )

