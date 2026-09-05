#!/usr/bin/env python3
"""
Authentication Service for SmartHome Dashboard
Provides URL secret-key authentication, auto-persistent cookies, and crawler protection.
"""

import os
import json
import secrets
import hmac
import hashlib
import ipaddress
import urllib.parse
from http.cookies import SimpleCookie

DIRECTORY = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(DIRECTORY, "config.json")
COOKIE_NAME = "sh_auth"
COOKIE_MAX_AGE = 315360000  # 10年 (秒)

def get_access_key() -> str:
    """config.json から access_key を取得、無ければ生成して保存"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("access_key"):
                    return str(data["access_key"])
        except Exception:
            pass

    key = secrets.token_urlsafe(16)
    try:
        data = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data["access_key"] = key
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Auth] Failed to persist access_key to config.json: {e}")
    return key

def get_expected_cookie_value(access_key: str = None) -> str:
    """access_key に基づく署名済み Cookie 値を計算"""
    if not access_key:
        access_key = get_access_key()
    return hmac.new(access_key.encode("utf-8"), b"smarthome_auth_cookie_v1", hashlib.sha256).hexdigest()

def is_trusted_private_ip(ip_str: str) -> bool:
    """IP アドレスがループバックまたはプライベートネットワークか判定"""
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_loopback or ip.is_private
    except ValueError:
        return False

def check_request_auth(headers, client_address, raw_path: str) -> dict:
    """
    リクエストが認証されているかを検証。
    戻り値:
    {
        "authenticated": bool,
        "set_cookie": bool,
        "clean_url": str | None,
        "cookie_value": str,
        "reason": str
    }
    """
    access_key = get_access_key()
    expected_cookie = get_expected_cookie_value(access_key)

    # 0. PWA インストール用パブリックアセット判定 (manifest.json, アイコン, sw.js)
    # Chrome や WebAPK 生成サーバーが Cookie なしで取得しに来るため、
    # 家電操作APIやHTML以外の安全なPWAメタデータのみパブリック配信を許可。
    parsed = urllib.parse.urlparse(raw_path)
    clean_p = parsed.path
    if clean_p.startswith('/dashboard'):
        clean_p = clean_p[len('/dashboard'):] or '/'

    pwa_assets = (
        '/manifest.json',
        '/sw.js',
        '/icon-192.png',
        '/icon-512.png',
        '/icon-maskable-192.png',
        '/icon-maskable-512.png',
        '/icon.svg',
        '/apple-touch-icon.png',
        '/favicon.ico',
    )
    if clean_p in pwa_assets:
        return {
            "authenticated": True,
            "set_cookie": False,
            "clean_url": None,
            "cookie_value": expected_cookie,
            "reason": "pwa_asset"
        }

    # 1. 真のローカル LAN 直接アクセス判定
    # Tailscale プロキシを経由している場合は X-Forwarded-For が付与されるため、
    # X-Forwarded-For が無く、かつ接続元がプライベート/ループバックIPなら宅内直接アクセスと判定。
    xff = headers.get("X-Forwarded-For")
    if not xff and is_trusted_private_ip(client_address[0]):
        return {
            "authenticated": True,
            "set_cookie": False,
            "clean_url": None,
            "cookie_value": expected_cookie,
            "reason": "local_direct"
        }

    # 2. Tailscale 認証済み端末 (Tailnet VPN 接続時)
    ts_user = headers.get("Tailscale-User-Login")
    if ts_user:
        return {
            "authenticated": True,
            "set_cookie": False,
            "clean_url": None,
            "cookie_value": expected_cookie,
            "reason": f"tailscale_user:{ts_user}"
        }

    # 3. HTTP ヘッダー認証 (API / CLI / Android アプリ等)
    auth_header = headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if hmac.compare_digest(token, access_key):
            return {
                "authenticated": True,
                "set_cookie": False,
                "clean_url": None,
                "cookie_value": expected_cookie,
                "reason": "bearer_header"
            }

    custom_key = headers.get("X-Access-Key", "")
    if custom_key and hmac.compare_digest(custom_key, access_key):
        return {
            "authenticated": True,
            "set_cookie": False,
            "clean_url": None,
            "cookie_value": expected_cookie,
            "reason": "custom_header"
        }

    # 4. 永続 Cookie 認証 (ブラウザ日常アクセス)
    cookie_header = headers.get("Cookie", "")
    if cookie_header:
        try:
            cookie = SimpleCookie()
            cookie.load(cookie_header)
            if COOKIE_NAME in cookie:
                cookie_val = cookie[COOKIE_NAME].value
                if hmac.compare_digest(cookie_val, expected_cookie):
                    return {
                        "authenticated": True,
                        "set_cookie": False,
                        "clean_url": None,
                        "cookie_value": expected_cookie,
                        "reason": "cookie"
                    }
        except Exception:
            pass

    # 5. URL クエリパラメータ認証 (?key=合言葉)
    parsed = urllib.parse.urlparse(raw_path)
    query_params = urllib.parse.parse_qs(parsed.query)
    url_keys = query_params.get("key", [])
    if url_keys and any(hmac.compare_digest(k, access_key) for k in url_keys):
        # 正しい合言葉パラメータを検出
        clean_qs = [(k, v) for k, v in urllib.parse.parse_qsl(parsed.query) if k != "key"]
        new_query = urllib.parse.urlencode(clean_qs)
        clean_url = parsed.path + (f"?{new_query}" if new_query else "")
        return {
            "authenticated": True,
            "set_cookie": True,
            "clean_url": clean_url,
            "cookie_value": expected_cookie,
            "reason": "url_key"
        }

    # すべての認証条件を満たさない場合（外部クローラー・未認証アクセス）
    return {
        "authenticated": False,
        "set_cookie": False,
        "clean_url": None,
        "cookie_value": expected_cookie,
        "reason": "unauthorized"
    }

def build_cookie_header(cookie_value: str, secure: bool = True) -> str:
    """Set-Cookie ヘッダー値を構築"""
    sec_flag = "; Secure" if secure else ""
    return f"{COOKIE_NAME}={cookie_value}; Max-Age={COOKIE_MAX_AGE}; Path=/; SameSite=Lax; HttpOnly{sec_flag}"
