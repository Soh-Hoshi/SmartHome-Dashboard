# SmartHome Dashboard - Project Memory & Development Guidelines

本ファイルは、ユーザーとのこれまでの開発履歴、設計思想、デザイン規約、ハードウェア仕様、ユーザーの好み、および実装状態をまとめた完全な引き継ぎ記憶ファイルです。次回以降のセッションでは、本ファイルを最優先で読み込んで開発を継続してください。

---

## 1. ユーザーの好み・設計思想（超重要）

1. **デザイン規約（Apple / Google Home 風の洗練されたダークUI）:**
   - **背景・カード色:** 背景 `#0d0f12`、カード `#1c1e23`、ホバー `#23262d`、モーダル内カード `#2a2d36`（ホバー `#323640`）、モーダル背景 `#1e2025`。
   - **角丸:** タイル・カード `rounded-3xl`（p-3.5）、ボトムシート `rounded-t-[32px] sm:rounded-[36px]`、ボタン `rounded-2xl`。
   - **ボーダー:** `border border-white/[0.03]` 〜 `border-white/[0.04]`。
   - **フォント・サイズ:** 見出し `text-base font-bold text-white px-1`、タイル名 `text-[15px] font-semibold text-white`、サブテキスト `text-xs text-neutral-400 font-normal`。
   - **カテゴリ制（Masonryレイアウト）:** ダッシュボード、シーン、オートメーションの全タブで `columns-1 md:columns-2 lg:columns-3 gap-6` ＋ `section` ＋ `h2` の1pxの狂いもない共通構造。
   - **余計なノイズの排除:** 装飾的なコネクタ線（縦線）や不要なバッジ（「フロー」等）は排除し、等高（高さ44px固定）のクリーンなカードリストに統一。

2. **アシスタント（Nova）の応答ルール ＆ アーキテクチャ:**
   - **ハイブリッド構成:** ①超高速ルールベース（0ms） ➔ ②Gemini 2.0 Flash API（無料枠、高度な意図解釈・会話対応） ➔ ③ローカルLLM（Ollama）フォールバック。
   - **確定情報のみを誠実に回答する:** システムが知り得ない未確定情報（例: 「ポストにある」など）を勝手に推測・断定してはいけない。
   - **鍵の所在:** 室内検知時は **「室内にあります」**、未検知時は **「室内にはありません」** と事実のみを即答。
   - **機器操作:** 画一的でシンプルな構文（例: 「リビングをオンにしました」「エアコンを冷房26℃に設定しました」）。

3. **実用ファースト・超高速スマートホーム設計（YAGNI原則）:**
   - **不要な説明モーダルの全廃:** 不特定多数向けの汎用アプリのような「ステップ詳細モーダル」や「複雑なフロー図」を排除し、個人専用の実用性・スピードを最優先。
   - **シーン（Scenes）:** タイルをタップした瞬間にその場で即実行（Apple Home風の快適な操作感）。
   - **オートメーション（Automations）:** タイル上で「有効/無効のトグルスイッチ」と「テスト実行ボタン」を直感操作。
   - **バックエンド（Python）:** 木月の体感温度（`feels_like`）や日没判定、在宅状態をダイレクトに判定し、最適なスマート空調・照明制御・消し忘れ通知を瞬時に実行。

---

## 2. 機器・ハードウェア仕様 ＆ 連携システム

1. **気象センサー（川崎市中原区木月）:**
   - 座標: `35.5647 N, 139.6544 E`
   - データソース: Open-Meteo API（JMA高精度モデル、APIキー不要、キャッシュ10分）
   - モジュール: `weather_service.py`（外気温、体感温度、天気、湿度、風速、日の出・日の入り、12時間予報）

2. **在宅確認センサー（スマートフォン LAN 検知）:**
   - IP: `192.168.0.30`、MAC: `72:58:BA:C7:40:FA` (SHG07)
   - 方式: 高速ARP/ICMPプローブ（2秒間隔、外出猶予30秒）
   - モジュール: `presence_service.py`

3. **鍵トラッカー（Tile Mate BLE Bluetooth）:**
   - 識別子: Tile, Inc. UUID `0000feed-0000-1000-8000-00805f9b34fb`（MACアドレス定期ローテーション対応・動的追跡方式）
   - 方式: BlueZの静的キャッシュを排除し、`bluetoothctl` によるリアルタイム BLE ライブスキャンパケットで即時判定。
   - モジュール: `tile_service.py`

4. **オートメーション（日本の祝日判定対応）:**
   - モジュール: `automation_service.py`（バックグラウンド監視）
   - 設定ファイル: `automations_config.json`
   - 実装済みルール:
     - **`平日 6:30`**: 日本の平日（土日祝除く）06:30にリビングライト点灯
     - **`平日 9:00`**: 日本の平日（土日祝除く）09:00にロボット掃除機（Eufy RoboVac G30）自動起動 ＋ Androidプッシュ通知
     - **`外出時`**: 在宅 ➔ 外出 変化時に稼働機器（照明/エアコン/ヒーター）を検知し、Nova Assist にアクションボタン付き消し忘れ警告通知を送信

5. **エアコン・ヒーター・照明・クリーナー:**
   - エアコン: SwitchBot API連携（冷房/除湿/オフ、22〜28℃）
   - ヒーター: スマートプラグ/赤外線（暖房/オフ、エコ、パワー）
   - 照明: リモコンAPI（全灯、常夜灯、明るさ上下）
   - クリーナー: Eufy RoboVac G30（掃除開始、一時停止、帰還、探す）

6. **Nova Assist (Android ネイティブアプリ) & 通知システム:**
   - パス: `android_bridge/` (Kotlin 1.9, Java 17, minSdk 26, targetSdk 34)
   - 機能: Android デフォルトデジタルアシスタント ＋ サーバープッシュ通知常駐受信
   - 常駐方式: `NotificationService` (Foreground Service, `dataSync` 属性, 端末起動時 `BootReceiver` 自動常駐)
   - 通信方式: 外部ライブラリ依存ゼロ (`HttpURLConnection` による `/api/notifications/stream` SSE ＋ `/api/notifications/poll` 自動フォールバック)
   - 通知方針: **PWA (WebPush/ServiceWorker) 通知は廃止・完全無効化し、Nova Assist ネイティブアプリへ一本化**（二重通知やブラウザ通知の不具合を防止）。
   - 高機能ネイティブ通知対応:
     - 🔘 **アクションボタン (`actions`)**: 通知タップでアプリを開かず裏で家電操作をバックグラウンド実行（`NotificationActionReceiver` 経由）。
     - 💬 **インライン返信 (`RemoteInput`)**: 通知内の入力欄から直接テキスト入力して Nova アシスタントに指示。
     - 📊 **プログレスバー (`progress`)**: 掃除機の進捗やタイマーなどの進行状況バー表示。
     - 🔄 **インプレース動的更新 (`id`)**: 同一 ID の通知を上書き更新（「⏳ 実行中...」➔「✅ 完了」へその場更新）。
   - 堅牢化・Hardening 済み仕様 (2026-09):
     - 🛡️ **二重/空通知抑止**: SSE `connected` ハンドシェイク時の `server_time` 同期と空メッセージ通知防止。
     - ⏱️ **タイムアウト・切断検知**: `readTimeout = 45000`（15秒keepalive×3回で無音切断を早期検知し再接続）。
     - 🕒 **時計ズレ耐性**: `last_poll_ts` の `SharedPreferences` 永続化と接続時キャッチアップポーリング。
     - 🔕 **過剰チャイム防止**: インプレース更新・プログレス進行時の `setOnlyAlertOnce(true)` 適用。
     - 🔗 **ディープリンク & 起動復元**: `onNewIntent` 実装および通知タップ時 `TARGET_URL` 伝達。
     - 🔒 **安全なID生成 & 例外保護**: ID 1001（常駐通知）との衝突防止マスク、Android 13+ の `SecurityException` 捕捉。
     - 🌐 **Tailscale Funnel サブパス保護**: `getBaseUrl()` で `/dashboard` を保持し、404 エラーを防止。
     - ⚡ **サーバー安定化**: LiveReload SSE keepalive、`push_service` キューサイズ上限 (100)、`daemon_threads = True`。
   - CLI操作: `smarthome notification [タイトル] <メッセージ>` または `smarthome notify <メッセージ> [オプション: --title, --progress, --action, --reply, --test-away, --test-progress]`
   - テストスイート: `python3 test_notifications_e2e.py`（全7項目: 通常通知、インプレース更新/プログレス、アクション/返信、アシスタント実行、ポーリング、並行リアルタイムSSE、Tailscale互換性）
   - 自動ビルド: GitHub Actions (`.github/workflows/build_apk.yml`) ➔ Release `android-latest` に `NovaAssist.apk` を自動発行

---

## 3. 開発運用ルール（安全策）

- **バックアップの維持:** `index.html` 編集時は必ず `cp index.html index.html.bak` を実行。
- **構文テスト:** 変更後は `HTMLParser` および JS ブラケット整合性テストを実施。
- **統合テスト:** 通知システム・バックエンド変更後は `python3 test_notifications_e2e.py` を実行。
- **Git同期:** テスト通過後、必ず Git にコミット＆プッシュ（`Soh-Hoshi/SmartHome-Dashboard`）。
- **常駐プロセス:** `python3 serve.py`（ポート 8080、`systemctl --user restart dashboard.service`）。
