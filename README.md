# SmartHome Dashboard & Assistant (NOVA)

Apple/Google Home風ダークテーマUI。家電・PC電源・センサー統合スマートホームダッシュボード。

## 機能

**ダッシュボード（カテゴリ制Masonryレイアウト）**
- PC: Wake-on-LAN起動、SSH経由スリープ/再起動/シャットダウン、デュアルブート(Win/Bazzite)OS切替
- 家電: リビング照明(5段階)・エアコン(SwitchBot API)・ヒーター・クリーナー(Eufy RoboVac G30)
- センサー: 気象(川崎市中原区木月/Open-Meteo JMA)・在宅確認(ARP/ICMP 2秒間隔)・鍵トラッカー(Tile Mate BLE)

**オートメーション**
- 平日06:30: リビング照明自動点灯
- 平日09:00: クリーナー自動起動
- 外出時消し忘れ防止: 照明/エアコン稼働中のみ通知送信→「いってきます」ワンタップで一括停止

**スマートシーン**: おはよう/おやすみ/いってきます/ただいま

**アシスタント「NOVA」**: ルールベース(0ms) + Gemini 2.0 Flash(無料枠) + Ollamaフォールバック

**PWA & Nova Assist**: Android常駐ネイティブアプリによるプッシュ通知

## ファイル構成

| ファイル | 役割 |
| :--- | :--- |
| `index.html` | Tailwind CSS + Material Symbols フロントエンド |
| `serve.py` | HTTP & REST API / SSE サーバー (Port: 8080) |
| `pc_service.py` | PC電源管理 (WoL, SSH非同期制御, OS状態監視) |
| `usb_service.py` | USBリレースイッチ制御 (デュアルブートOS選択) |
| `auth_service.py` | HMAC署名Cookie認証 & クローラー遮断 |
| `state_manager.py` | 家電/PC/センサー状態管理 & JSON永続化 |
| `push_service.py` | Nova Assist通知キューイング & 配信 |
| `weather_service.py` | 気象データ取得・キャッシュ (Open-Meteo JMA) |
| `presence_service.py` | スマートフォンLAN検知 (2秒間隔プローブ) |
| `tile_service.py` | Tile Mate BLEリアルタイムスキャン |
| `automation_service.py` | 日本祝日判定 & オートメーション |
| `assistant_engine.py` | NOVAエンジン (Gemini 2.0 Flashハイブリッド) |
| `switchbot_client.py` | SwitchBot APIクライアント |
| `eufy_client.py` | Eufy RoboVac G30ローカルプロトコル |
| `PROJECT_MEMORY.md` | プロジェクト記憶・設計規約・引き継ぎ |

## ネットワーク構成

```
クライアント → HTTPS → Cloudflare → Oracle Cloud VPS(168.110.50.171)
→ Nginx → FRP Server(18080) → FRP Tunnel → 自宅frpc(192.168.0.10)
→ Port 8080 → serve.py
自宅LAN(192.168.0.0/24): PC(192.168.0.20), SwitchBot, Eufy, Tile, Phone
```

- Web: `https://home.sohhoshi.com`
- ストリーミング: `https://stream.sohhoshi.com` (Sunshine/Moonlight)

## 起動

```bash
systemctl --user status dashboard.service
systemctl --user restart dashboard.service
journalctl --user -u dashboard.service -f
```

## CLIコマンド (`/home/soh/dashboard/smarthome`)

```bash
smarthome pc status|on|sleep|restart|off
smarthome light on|off
smarthome ac 26
smarthome heater on
smarthome cleaner start
smarthome nova "おはよう"
smarthome nova "鍵ある？"
```
