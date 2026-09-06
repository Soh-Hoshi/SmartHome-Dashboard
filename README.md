# 🏡 SmartHome Dashboard & Assistant (NOVA)

洗練された Apple / Google Home 風ダークテーマ UI と、実機家電・PC 電源管理・各種センサー連携を備えた統合スマートホーム・ダッシュボード＆AIアシスタントシステムです。

---

## ✨ 主な機能と特徴

### 1. 📊 統合ダッシュボード（カテゴリ制 Masonry レイアウト）
- **スイッチ（PC 電源 ＆ OS 管理）**:
  - 🖥️ **デスクトップ PC**: Wake-on-LAN（起動）、超高速スリープ・再起動・シャットダウン（SSH 経由・非同期実行で即応）。
  - 🔀 **デュアルブート（Windows / Bazzite）**: USB 物理スイッチと連動し、次回起動 OS をワンタップで切り替え。
- **家電コントロール**:
  - 💡 **リビング照明**: 点灯/消灯、全灯、常夜灯、5段階の明るさ調節。
  - ❄️ **エアコン**: SwitchBot API 連携。冷房/暖房/除湿/停止、直感的な蹄型（Horseshoe）温度ゲージ。
  - 🔥 **ヒーター**: 暖房/停止、エコモード、パワー調節（弱/中/強）。
  - 🤖 **ロボット掃除機**: Eufy RoboVac G30 実機連携。清掃開始/一時停止/帰還、吸引力切り替え、探す（Beep）機能。
- **センサー類（気象 ➔ 在宅確認 ➔ 鍵）**:
  - 🌦️ **気象センサー**: 川崎市中原区木月のリアルタイム外気温・体感温度・天気・湿度・風速・日の出/日の入り、および 12時間ごとの詳細予報（Open-Meteo JMA高精度モデル）。
  - 📱 **在宅確認センサー**: スマートフォン（SHG07）の高速 ARP/ICMP プローブ（2秒間隔）による、外出・帰宅の即時リアルタイム判定。
  - 🔑 **鍵トラッカー**: Tile Mate (Bluetooth BLE) のライブスキャンによる室内検知判定。

---

### 2. ⚡ オートメーション（日本の祝日判定 ＆ 在宅検知連動）
- **平日 06:30（おはよう照明）**: 日本の平日（土日祝除く）朝 06:30 にリビング照明を自動点灯。
- **平日 09:00（自動清掃）**: 日本の平日朝 09:00 に Eufy クリーナーを自動出撃させ床清掃を開始。
- **外出時消し忘れ防止**: 在宅から外出（不在）への変化を検知した際、照明やエアコンがついたままの場合にスマホへ通知をプッシュ送信。**通知内の「🚪 いってきます（全消灯）」ボタンからワンタップで即座に一括停止**が可能。

---

### 3. 🌅 スマートシーン
- **ワンタップ実行 ＆ アクションフロー可視化**:
  - 🌅 **おはよう**: リビング照明オン ＋ 外気温・体感温度に基づくスマート空調自動判断
  - 🌙 **おやすみ**: リビング照明オフ ＋ 就寝向けスマート空調（冷房27℃等）
  - 🚪 **いってきます**: 照明・エアコン・ヒーターの完全一括停止
  - 🏠 **ただいま**: 日没後のみリビング点灯 ＋ 快適スマート空調
- **フローシート**: 「何がどの順番でどう動くか」をノイズのない等高カードリストで確認可能。

---

### 4. 🗣️ スマートアシスタント「NOVA」
- **自然言語による家電・PC操作**:
  - 「電気つけて」「エアコン26度」「ヒーター消して」「掃除機かけて」「パソコンつけて」「PCスリープして」
- **確定事実に基づく誠実な返答**:
  - 「鍵ある？」 ➔ **「室内にあります」** / **「室内にはありません」**（未確定な推測を言わず、検知事実のみを即答）
- **ミリ秒応答のルールベース ＋ Gemini 2.0 Flash（無料枠）ハイブリッドインテリジェンス**。

---

### 5. 📱 PWA ＆ Nova Assist 常駐通知
- **ホーム画面への追加（PWA）**:
  - Safari / Chrome の「ホーム画面に追加」で、URLバーのない洗練された全画面ネイティブアプリ感覚で操作可能。
- **Nova Assist (Android ネイティブアプリ) 連動**:
  - Android ネイティブ常駐サービス（SSE/Poll）と連携し、外出検知時の消し忘れアラートなどを高信頼でプッシュ通知。

---

## 🛠️ システム構成・アーキテクチャ

| ファイル | 役割 |
| :--- | :--- |
| `index.html` | Tailwind CSS ＋ Material Symbols による洗練された Apple/Google Home 風フロントエンド UI |
| `serve.py` | LiveReload 対応 HTTP ＆ REST API / SSE 通知サーバー（Port: 8080） |
| `pc_service.py` | PC 電源管理サービス（WoL起動、SSH非同期スリープ/シャットダウン/再起動、OS状態監視） |
| `usb_service.py` | USB 物理リレースイッチ制御サービス（デュアルブート OS 選択用ハードウェア連携） |
| `auth_service.py` | 外部リモートアクセス時のセキュリティ認証 ＆ HMAC 署名 Cookie 管理 |
| `state_manager.py` | 家電・PC・センサー状態の一元管理 ＆ JSON 永続化 |
| `push_service.py` | Nova Assist 向け通知キューイング ＆ 配信管理サービス |
| `weather_service.py` | 川崎市中原区木月の気象データ取得・キャッシュ（Open-Meteo JMA モデル） |
| `presence_service.py` | スマートフォンの高速 LAN 検知（2秒間隔プローブ ＆ 外出検知連動） |
| `tile_service.py` | Tile Mate BLE リアルタイムスキャン判定 |
| `automation_service.py` | 日本の祝日判定 ＆ 朝照明・朝清掃・外出時消し忘れ防止オートメーション |
| `assistant_engine.py` | 自然言語アシスタント「NOVA」エンジン（Gemini 2.0 Flash ハイブリッド） |
| `switchbot_client.py` | SwitchBot API（エアコン操作）クライアント |
| `eufy_client.py` | Eufy RoboVac G30 ローカルプロトコル連携クライアント |
| `PROJECT_MEMORY.md` | プロジェクト記憶・設計思想・デザイン規約の永続化ファイル |

---

## 🌐 ネットワーク・外部アクセス構成

```mermaid
graph LR
    User[📱 クライアント] -->|HTTPS| CF[Cloudflare CDN]
    CF -->|SSL| VPS[Oracle Cloud VPS<br/>168.110.50.171]
    VPS -->|Nginx Reverse Proxy| FRPs[FRP Server<br/>Port: 18080]
    FRPs -->|FRP Tunnel| FRPc[自宅サーバー frpc<br/>192.168.0.10]
    FRPc -->|Port: 8080| Dashboard[Dashboard HTTP Server<br/>serve.py]
    
    subgraph 自宅LAN (192.168.0.0/24)
        Dashboard -->|WoL / SSH| PC[デスクトップPC<br/>192.168.0.20]
        Dashboard -->|USB Relay| Switch[USB スイッチ]
        Dashboard -->|SwitchBot API| AC[エアコン / 照明]
        Dashboard -->|Local Protocol| Eufy[RoboVac G30]
        Dashboard -->|BLE Scan| Tile[Tile Mate]
        Dashboard -->|ARP/ICMP| Phone[スマートフォン]
    end
```

- **Web ダッシュボード**: `https://home.sohhoshi.com`
- **リモートゲームストリーミング**: `https://stream.sohhoshi.com`（Sunshine / Moonlight）

---

## 🚀 起動方法と使い方

### サーバーの起動 (Systemd User Service)
通常はバックグラウンドサービスとして自動起動・常駐しています。

```bash
# 状態確認
systemctl --user status dashboard.service

# 再起動
systemctl --user restart dashboard.service

# ログ確認
journalctl --user -u dashboard.service -f
```

---

### CLI からの操作（`smarthome` コマンド）

`/home/soh/dashboard/smarthome` から直接デバイスの操作やアシスタントの呼び出しが可能です。

```bash
# PC 電源操作
smarthome pc status         # PC の電源状態と OS を確認
smarthome pc on             # PC を起動 (Wake-on-LAN)
smarthome pc sleep          # PC をスリープ
smarthome pc restart        # PC を再起動
smarthome pc off            # PC をシャットダウン

# 家電操作
smarthome light on          # リビング照明点灯
smarthome light off         # リビング照明消灯
smarthome ac 26             # エアコン冷房 26℃
smarthome heater on         # ヒーター点灯
smarthome cleaner start     # クリーナー清掃開始

# アシスタント NOVA への呼びかけ
smarthome nova "おはよう"
smarthome nova "鍵ある？"
smarthome nova "リビングの電気を消して"
smarthome nova "PCをスリープして"
```
