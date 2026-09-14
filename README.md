# SmartHome Dashboard & Assistant (Nova)

ダークテーマUIを採用した、家電・PC電源・センサー統合スマートホームシステムおよび専用クライアント。

## 概要

本システムは、自宅サーバーで稼働するバックエンド（Python）と、モダンWeb技術で構築されたダッシュボード（Vue 3 + TypeScript + Tailwind CSS）、およびAndroid統合アプリ「Nova Assist」で構成されています。

## 主な機能

### 1. ダッシュボード
- **PC電源管理**: Wake-on-LANによる起動、SSH経由のスリープ・再起動・シャットダウン、デュアルブートOS切替（Windows / Bazzite）
- **家電操作**: リビング照明（明るさ5段階・常夜灯）、エアコン（冷房/除湿/暖房/オフ・風量・温度設定）、ヒーター（暖房/オフ・エコ/パワー）、ロボット掃除機（開始/一時停止/ホーム/吸引力設定/探す）
- **センサー監視**: 気象情報（川崎市中原区木月 / Open-Meteo JMA）、在宅確認（スマートフォンARP/ICMP監視による在宅・外出判定）、鍵トラッカー（Tile Mate BLEリアルタイム検知）
- **スマートシーン**: おはよう、おやすみ、いってきます、ただいまの一括制御
- **オートメーション**: 日本の祝日を考慮した平日自動制御（照明点灯、掃除機起動、外出時の消し忘れ検知など）

### 2. 音声アシスタント「NOVA」
- ルールベース高速応答（0ms）とGemini 2.0 Flash（LLM）のハイブリッド構成（Ollamaローカルフォールバック対応）
- 音声入力による家電操作、PC電源操作、室内状態確認

### 3. Android 統合クライアント「Nova Assist」
ダッシュボード閲覧、常駐プッシュ通知、デジタルアシスタントを1つのアプリに統合しています。

- **フルスクリーンダッシュボード**: アプリ起動で即座にダッシュボードを表示
- **デジタルアシスタント**: Androidの「デフォルトのデジタルアシスタントアプリ」に設定可能。電源ボタン長押しやナビゲーションジェスチャーから即座にNova音声入力が起動
- **常駐通知**: サーバーからのSSE接続によるリアルタイム通知。外出時の消し忘れ警告（「いってきます」「Novaへ指示」のインライン操作）や各種ステータス通知を受信

#### Nova Assist インストール手順
1. 本リポジトリの [Releases](../../releases) から最新の `NovaAssist.apk` をダウンロードしてインストール
2. 初回起動時にマイクおよび通知の権限を許可
3. Androidの「設定」→「アプリ」→「デフォルトアプリ」→「デジタルアシスタントアプリ」で「Nova Assist」を選択
4. 電源ボタン長押し等のショートカットでアシスタントが起動可能になります

## アーキテクチャ・ネットワーク構成

```
クライアント（Webブラウザ / Nova Assist APK）
    ↓ HTTPS (home.sohhoshi.com)
Cloudflare
    ↓
Oracle Cloud VPS
    ↓ FRP Tunnel
自宅サーバー (Port 8080 / serve.py)
    ├─ frontend/dist (Vue 3 フロントエンド)
    ├─ 各種センサー・機器制御 API
    └─ 自宅LAN (PC, SwitchBot, Eufy, Tile, Android)
```

## サーバー起動・管理

```bash
# サービスのステータス確認
systemctl --user status dashboard.service

# サービスの再起動
systemctl --user restart dashboard.service

# ログの確認
journalctl --user -u dashboard.service -f
```

## CLIコマンド (`smarthome`)

```bash
smarthome pc status|on|sleep|restart|off
smarthome light on|off
smarthome ac 26
smarthome heater on
smarthome cleaner start
smarthome nova "おはよう"
smarthome nova "鍵ある？"
```
