# SmartHome Dashboard & Nova Assist - セッション引き継ぎサマリー (2026-09-04)

本ドキュメントは、2026年9月4日の開発セッションで実施した全作業の流れ、設計変更、現在の稼働状態、および次回再開時の確認事項をまとめた引き継ぎ記録です。

---

## 1. 今回の流れ・実施タスク（時系列）

### ① 通知システム ＆ Android Bridge の徹底監査・堅牢化（Bug Fixes & Hardening）
前セッションで実施された監査レポート（DeepInvestigator）の分析に基づき、以下の重大な不具合の修正と耐久性向上を実施しました。

1. **Android アプリ復元時の音声アシスタント起動不良の解消 (`MainActivity.kt`)**:
   - `AssistActivity` から `FLAG_ACTIVITY_CLEAR_TOP` で遷移した際、アプリがバックグラウンドに常駐していると `onCreate()` ではなく `onNewIntent()` が呼ばれる仕様でした。
   - `onNewIntent(intent)` を実装し、音声起動パラメータ（`?assist=1`）やディープリンク URL が破棄される不具合を完全解消。
2. **SSE 接続時の二重・空通知バグの解消 (`NotificationService.kt`)**:
   - サーバー接続ハンドシェイク（`{"status":"connected"}`）を受信した際、クライアントが空の「SmartHome」通知を表示していた問題を修正。
   - サーバーから `server_time` を送信し、接続時に端末の時計ズレを補正する処理へ改修。
3. **無音切断・モバイル回線ドロップ対策 (`NotificationService.kt`)**:
   - `readTimeout = 45000`（45秒）を設定。サーバーの15秒 keepalive を3回受信できない場合に TCP ソケット切断を能動的に検知し、自動再接続ループへ遷移。
4. **起動時の通知バースト抑止 & 時計ズレ耐性 (`NotificationService.kt`)**:
   - `last_poll_ts` を `SharedPreferences` に永続化。アプリ再起動時に過去の通知（最大50件）が一気に鳴動・再表示される事故を完全に防止しつつ、接続直後に最新の未読通知をキャッチアップ取得。
5. **過剰チャイム・バイブレーションの抑止 (`NotificationService.kt`, `NotificationActionReceiver.kt`)**:
   - `.setOnlyAlertOnce(true)` を適用。掃除機のプログレスバー進行（20% -> 50% -> 100%）やアクション実行中（⏳ -> ✅）のインプレース更新時に、毎回バイブが鳴り響く不快な挙動を解消。
6. **通知 ID のオーバーフロー・常駐通知上書き事故の防止 (`NotificationService.kt`)**:
   - 通知 ID を正数マスク（2000〜101999）に正規化。Foreground Service の常駐通知 ID（1001）をユーザー通知が誤って上書き・終了させてしまう致命的リスクを排除。
7. **Tailscale Funnel サブパス消失による 404 エラーの防止 (`NotificationService.kt`, `NotificationActionReceiver.kt`)**:
   - `getBaseUrl()` でホスト名のみ抽出しパスを削除していたため、`/dashboard` サブパスが脱落して Tailscale エッジから 404 が返るリスクを解消（`/dashboard` を正しく保持）。
8. **アクション完了通知のタップ動作保証 (`NotificationActionReceiver.kt`)**:
   - 通知カードに `contentIntent`（アプリ起動）を設定。これにより Android OS 上で `setAutoCancel(true)` が正常に動作し、タップで通知が消えてダッシュボードが開くように改善。
   - Android 13+ の通知権限例外（`SecurityException` 等）を安全に try-catch。
9. **バックエンドの通知パラメータ転送完備 (`push_service.py`, `serve.py`, `smarthome`)**:
   - `dispatch_internal_api` および CLI の `direct_fallback` において、`actions`, `id`, `progress`, `ongoing`, `auto_cancel` が脱落していたのを完全転送に改修。
   - `push_service` の SSE クライアントキューに `maxsize=100` を設定（メモリリーク防止）。
   - インプレース更新時に履歴配列の末尾に再追加し、時系列順序を維持。
   - LiveReload SSE に 20秒間隔の keepalive を追加し、ブラウザ切断時のスレッドリークを防止。`server.daemon_threads = True` を設定。
10. **全7項目の E2E 統合自動テストスイート新設 (`test_notifications_e2e.py`)**:
    - 通常通知、インプレース更新、プログレスバー、アクション/インライン返信、アシスタントAPI実行、フォールバックポーリング、リアルタイム並行SSE配信、Tailscaleサブパス互換性の全テストを自動化（全項目 PASS）。

---

### ② オートメーション「平日 9:00」（ロボット掃除機起動）の実装
- **設定 (`automations_config.json`)**:
  - `weekday_morning_cleaner`（日本の平日〈土日祝除く〉09:00 JST / Eufy RoboVac G30 起動）を登録。
- **バックグラウンドスケジューラー (`automation_service.py`)**:
  - 祝日・振替休日判定を組み込んだスケジューラーが 09:00 に自動検知し、`/api/cleaner` (`action: start`) を実行。
  - 実行時に Nova Assist へ「平日 9:00：ロボット掃除機を開始しました。」のプッシュ通知を送信。
- **ダッシュボード画面 (`index.html`)**:
  - 「デイリー」セクション内に等高・Apple Home 風のカードタイルを追加（SVG ロボット掃除機アイコン）。
  - 右側の ▶ 再生ボタンから即座にテスト実行可能。

---

### ③ 外出時消し忘れ通知 ＆ 通知全般の極限シンプル化
ユーザーのご要望（「通知のボタン、novaではなくNovaに修整」「リビング照明とかの説明もいらない。タイトルとボタン類だけ」「あとその他の通知に関してもアイコン類は要らない」）に基づき、徹底的に洗練・最適化を実施しました。

1. **消灯時スキップ**:
   - 外出検知時、照明・エアコン・ヒーターがすべて OFF の場合は通知送信を完全スキップ。
   - 稼働中の機器がある場合のみ通知を発行。
2. **本文・説明文の全廃（タイトルとボタン類のみ）**:
   - 「リビング照明」等の機器名や説明文を全廃。
   - **タイトル**: `お出かけですか？`
   - **本文**: なし（空文字）
   - **Android Bridge**: `message` が空の場合は `setContentText` および `BigTextStyle` を呼び出さず、タイトルとアクションボタンのみを無駄な余白なくスマートに描画。
3. **アクションボタンのシンプル化 & 表記修整**:
   - 「そのまま」ボタンを削除。
   - ボタン表記を小文字から修整: **「いってきます」** と **「Novaへ指示」** （Novaを大文字に統一）。
4. **その他の通知も含めたアイコン・絵文字の完全排除**:
   - Android Bridge (`NotificationActionReceiver.kt`): アクション実行中（`実行中: ...`）、実行完了（`実行完了`）、エラー（`エラー`）の各通知から絵文字（⏳, ✅, ⚠️）を排除。
   - アクションボタンのアイコン（Icon）を常に 0（非表示）に設定。
   - CLI通知ヘルプやロボット掃除機タイトル等（🤖 等）からも絵文字を排除。

---

### ④ 全体名称のダッシュボード表記統一 ＆ シーン応答文の短縮・改行
ユーザーのご要望（「全体的にロボット掃除機の名称はクリーナーにしてほしい」「ダッシュボード上の名前に全体を通して統一」「シーンを実行したときの文が長い。短くするか、改行して短くする」）を完全に反映しました。

1. **名称のダッシュボード完全統一**:
   - ロボット掃除機 / 掃除機の表記をすべてダッシュボード表記である **「クリーナー」** に統一（`automation_service.py`, `assistant_engine.py`, `smarthome` CLI）。
   - ライトの表記もダッシュボード表記である **「リビング照明」** に統一。
2. **シーン実行時の応答メッセージの短縮 ＆ 改行**:
   - 通知カードやアシスタントで長文が詰まるのを解消。冗長な理由説明（体感温度や就寝用設定等）を省き、**「挨拶」＋「改行」＋「短い実行結果」**（1行10〜15文字程度）にスッキリ整理。
   - 例：
     - **いってきます**: `いってらっしゃい！\n照明と空調を停止しました。`
     - **おはよう**: `おはようございます！\n照明を点灯し、エアコンを設定しました。`
     - **おやすみ**: `おやすみなさい。\n照明を消灯し、エアコンを設定しました。`
     - **ただいま**: `おかえりなさい！\n照明を点灯し、エアコンを設定しました。`

### ④ クローラー遮断 ＆ シークレットキー（合言葉）永続Cookieホワイトリスト (2026-09-05)
Tailscale Funnel（外部公開）経由で巡回ボットがアクセスし、HTML内のボタンをクリック走査して家電が誤動作した問題に対し、**「ログイン画面を出さずにクローラーを100%遮断する」**ホワイトリスト方式を実装・検証完了しました。

1. **アーキテクチャ**:
   - **`auth_service.py`**:
     - `config.json` の `access_key` を合言葉として管理。
     - HMAC-SHA256 署名付きの永続 Cookie（`sh_auth`、有効期限10年、HttpOnly, Secure）を発行・検証。
   - **`serve.py` の多層認証判定**:
     - **宅内LAN直接アクセス**: `X-Forwarded-For` が無くプライベートIPからの直接通信は無条件パス。
     - **Tailscale VPN接続端末**: `Tailscale-User-Login` ヘッダー付きのリクエストは無条件パス。
     - **ブラウザ日常アクセス**: Cookie（`sh_auth`）があれば無条件パス。
     - **初回アクセス**: `https://server.tail52d127.ts.net/dashboard/?key=<合言葉>` でアクセスすると、Cookieを発行しURLから `?key=...` を消去した `/dashboard/` へ 302 リダイレクト。
     - **外部クローラー/ボット**: Cookieもキーも無いため、HTMLやAPIを一切返さず即座に `403 Forbidden` で切断。
2. **Nova Assist (Android Bridge) 連携**:
   - `NetworkUtils.kt` を新設。WebView の CookieManager からセッション Cookie を取得して `HttpURLConnection`（SSE / Polling / ActionReceiver）に自動付与。
   - 設定 URL に `?key=...` が含まれる場合は `X-Access-Key` ヘッダーとしてもフォールバック送信。
   - Android APK を再ビルド（3.2MB、ビルド成功）。
### ⑤ Nova Assist HTTPエラー解消 ＆ スマホ版Novaバー完全一致UI改修 (2026-09-08)
ユーザーからのご指摘（「コマンド送ろうとすると、httpエラーが出る」「uiがダッシュボードのスマホのnovaのバーとデザインが違うのが嫌だ（文字入力来た時に青い目立つ送信ボタンが出るのが嫌です。）」）に基づき、原因を徹底特定し完全修正を実施しました。

1. **HTTPエラー (403 Forbidden) の根本原因と解決**:
   - **原因**: 外部回線（Tailscale Funnel / 外部IP `210.157.194.129`）経由で Android ネイティブアプリから送信されるリクエスト（`/api/assistant`, `/api/notifications/stream` 等）に合言葉（`Tamago1341`）が付与されておらず、サーバーのクローラー遮断ホワイトリスト判定で `reason=unauthorized` となり 403 拒否されていた。
   - **対策 (`NetworkUtils.kt`, `MainActivity.kt`)**:
     - `DEFAULT_ACCESS_KEY = "Tamago1341"` をアプリ内に定義。
     - `NetworkUtils.getAccessKey(context)` により、端末内に保存された合言葉、またはデフォルト合言葉を確実に取得。
     - `applyAuthHeaders` で `X-Access-Key: Tamago1341` および `User-Agent: NovaAssist-Android/1.0` を常時付与。
     - `MainActivity.kt` 起動時にキーを同期し、CookieManager のディスク同期（`flush()`）を完備。
2. **スマホ版Novaプロンプトバーとのデザイン完全統一 ＆ 青い送信ボタンの全廃**:
   - **左側アイコン**: ダッシュボードの `w-10 h-10 rounded-full bg-white/[0.05]` と同一の 40dp 円形薄白コンテナ（`@drawable/bg_sparkle_container`）を新設し、中央にキラキラアイコン（22dp、`#2196f3`）を配置。
   - **青い目立つ送信ボタンの完全廃止**: 文字入力時に全面青（`#2196f3`）の円形ボタンに変化していた処理（`bg_mic_button_send`）を完全撤廃。文字入力時もダッシュボードと全く同じダークグレー（`#1e2128`、ボーダー `#0Dffffff`）のマイクボタンをそのまま維持。
   - **操作性の両立**: 見た目はダッシュボードと100%同一のまま、文字入力時はキーボードの Enter / 送信 に加え、右端ボタンのタップでも直感的に送信（`submitCommand`）される洗練されたUXを実現。
   - **バーの形状・ヒント**: 縦幅 58dp、左右余白 8dp、プレースホルダー `Novaに話しかける...`（色 `#94a3b8`）に統一。
   - **バージョン更新**: `1.0.3` (code 9)。Debug (3.1MB) / Release (2.5MB) ともにビルド成功。

---

## 2. 現在の稼働状態 ＆ Git 状況

| 項目 | 状態 | 備考 |
| :--- | :--- | :--- |
| **HTTP / SSE サーバー** | 🟢 稼働中 (Active: running) | systemd user サービス (`dashboard.service`), Port 8080 |
| **Android Bridge (Nova Assist)** | 🟢 接続準備完了 | デフォルト合言葉 `Tamago1341` 適用済み |
| **Android APK (Release)** | 🟢 ビルド成功 (2.5MB) | `android_bridge/app/build/outputs/apk/release/app-release.apk` (v1.0.3) |
| **Android APK (Debug)** | 🟢 ビルド成功 (3.1MB) | `android_bridge/app/build/outputs/apk/debug/app-debug.apk` (v1.0.3) |
| **認証テスト** | 🟢 PASS | `X-Access-Key` 外部経由認証 PASS |
| **Git ブランチ** | 🟢 main | コミット反映可能状態 |

---

## 3. 次回再開時のクイックリファレンス

次回作業を開始する際は、以下のファイルを確認すれば即座に状況を把握できます：
- [`PROJECT_MEMORY.md`](file:///home/soh/dashboard/PROJECT_MEMORY.md): プロジェクトの設計思想・ハードウェア仕様・開発運用ルールの正本。
- [`LATEST_SESSION_SUMMARY.md`](file:///home/soh/dashboard/LATEST_SESSION_SUMMARY.md): 本ドキュメント（直近の作業内容）。

### 主な動作確認コマンド
```bash
# サービスの稼働確認
systemctl --user status dashboard.service

# E2E 統合通知テストの実行
python3 /home/soh/dashboard/test_notifications_e2e.py

# 外出時通知の動作確認 (機器が消えていればスキップされる)
/home/soh/dashboard/smarthome notify --test-away

# クリーナーの操作確認
/home/soh/dashboard/smarthome cleaner start
/home/soh/dashboard/smarthome cleaner stop
```
