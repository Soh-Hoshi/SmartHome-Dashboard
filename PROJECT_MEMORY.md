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
     - **`外出時`**: 在宅 ➔ 外出 変化時に稼働機器（照明/エアコン/ヒーター）がある場合のみ通知（全消灯時は送信スキップ）。説明文や不要なボタン・アイコンを排除し、本文に稼働機器名のみを記載。アクションボタンは「いってきます」「novaへ指示」の2つに最適化。

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

---

## 4. 直近の開発経緯・セッション引き継ぎログ (2026-09-04)

### 4.1 通知システム ＆ Android Bridge の包括的堅牢化（Hardening）
- **背景**: Android ネイティブ通知（Nova Assist）の高機能化に伴う潜在バグの監査・改修。
- **改修内容**:
  1. `MainActivity.kt`: `onNewIntent` を実装。アプリがメモリ内にある状態でも、電源長押しやアシスタントジェスチャーで `?assist=1` が破棄されず正常に音声起動するように修正。
  2. `NotificationService.kt`:
     - SSE 接続時の `connected` ハンドシェイクで不要な空通知（SmartHome）が出る問題を抑止（`server_time` 同期）。
     - `readTimeout = 45000` を設定し、TCP サイレント切断を早期検知して自動再接続。
     - `last_poll_ts` を `SharedPreferences` に永続化し、起動時の過去通知バースト再生を防ぎつつ未読通知を補完。
     - `.setOnlyAlertOnce(true)` でプログレス更新時の連続バイブ/チャイムを抑止。
     - 通知 ID を正数（2000〜101999）にマスク正規化し、常駐サービス ID（1001）との衝突やオーバーフローを防止。
     - `getBaseUrl()` で `/dashboard` サブパスを維持し、Tailscale Funnel 経由での 404 エラーを防止。
     - アクションボタンのアイコン引数を `0`（非表示）に設定。
  3. `NotificationActionReceiver.kt`:
     - 更新通知に `contentIntent` を設定し、通知タップでアプリ起動可能かつ `setAutoCancel(true)` が OS 側で正常動作するように改修。
     - Android 13+ の `SecurityException` などの例外安全保護を追加。
  4. `push_service.py` / `serve.py` / `smarthome`:
     - SSE キュー上限（`maxsize=100`）でメモリリークを防止。
     - インプレース更新時に配列末尾に再配置し、時系列順序を維持。
     - `dispatch_internal_api` および CLI の `direct_fallback` でリッチ通知パラメータ（`actions`, `id`, `progress`, `ongoing`, `auto_cancel`）を漏れなく完全転送。
     - LiveReload SSE に 20秒間隔の keepalive を追加し、ブラウザタブ切断時のスレッドリークを防止。`server.daemon_threads = True` を設定。
  5. `test_notifications_e2e.py`:
     - 通常通知・インプレース更新・プログレスバー・アクション/返信・アシスタント実行・ポーリング・並行リアルタイムSSE配信・Tailscaleサブパス互換性の全7項目を自動検証するテストスイートを新設（常時 PASS を維持）。

### 4.2 オートメーション「平日 9:00」（ロボット掃除機起動）の追加
- **設定**: `automations_config.json` に `weekday_morning_cleaner` を追加（日本の平日〈土日祝除く〉09:00 JST）。
- **バックエンド**: `automation_service.py` で 09:00 に Eufy RoboVac G30 の掃除開始（`/api/cleaner` ➔ `action: start`）を実行し、Nova Assist へ完了プッシュ通知を送信。
- **フロントエンド**: `index.html` の「デイリー」セクションに等高・SVGクリーナーアイコン付きのカードタイルを追加し、右端の ▶ ボタンから即時テスト実行可能に。

### 4.3 外出時消し忘れ通知 ＆ 通知全般の極限シンプル化
- **消灯時スキップ**: 在宅 ➔ 外出 変化時、照明・エアコン・ヒーター等の電気がすべて消えている場合は通知を一切送信しない（稼働機器がある場合のみ送信）。
- **本文・説明文の全廃**: 「リビング照明」等の機器名や説明文を全廃。タイトル「お出かけですか？」とアクションボタンのみをコンパクトに表示。Android Bridge側でも本文が空の場合は `setContentText` / `BigTextStyle` を呼び出さず、タイトルとボタンのみを描画。
- **ボタンの整理**: 「そのまま」ボタンを削除。ボタン文言を「いってきます」「Novaへ指示」の2つに整理（大文字の「Nova」に統一）。
- **通知全般のアイコン・絵文字全廃**: 外出時通知のみならず、その他の通知（アクション実行中・完了・エラー通知、プログレス通知等）からも絵文字（⏳, ✅, ⚠️, 🤖 等）およびアクションボタンアイコンを完全排除。

### 4.4 現在の稼働状態
- **systemd サービス**: `dashboard.service`（Active: running, port 8080）。
- **Git リポジトリ**: すべての変更をコミットし、`origin/main` にプッシュ可能状態。
