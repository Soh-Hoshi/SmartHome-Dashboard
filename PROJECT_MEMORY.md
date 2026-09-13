# SmartHome Dashboard - Project Memory

次回セッション開始時に本ファイルを最優先で読み込むこと。

## 1. 設計規約・ユーザーの好み

**デザイン（Apple/Google Home風ダークUI）:**
- 背景: `#0d0f12` / カード: `#1c1e23` / ホバー: `#23262d` / モーダル内カード: `#2a2d36`(ホバー`#323640`) / モーダル背景: `#1e2025`
- 角丸: タイル`rounded-3xl`(p-3.5) / ボトムシート`rounded-t-[32px] sm:rounded-[36px]` / ボタン`rounded-2xl`
- ボーダー: `border border-white/[0.03]`〜`border-white/[0.04]`
- フォント: 見出し`text-base font-bold text-white px-1` / タイル名`text-[15px] font-semibold text-white` / サブテキスト`text-xs text-neutral-400 font-normal`
- レイアウト: 全タブ共通 `columns-1 md:columns-2 lg:columns-3 gap-6` + `section` + `h2`
- 装飾的コネクタ線・不要バッジ禁止。等高(44px固定)クリーンカードリストに統一

**NOVAアシスタント:**
- 構成: ①ルールベース(0ms) → ②Gemini 2.0 Flash(無料枠) → ③Ollama(フォールバック)
- 未確定情報を推測・断定禁止。確定事実のみ回答
- 鍵: 室内検知→「室内にあります」/ 未検知→「室内にはありません」
- 機器操作応答: 「リビングをオンにしました」「エアコンを冷房26℃に設定しました」

**実用ファースト原則:**
- 説明モーダル・複雑なフロー図禁止
- シーン: タップ即実行
- オートメーション: タイル上でトグル+テスト実行ボタン

## 2. ハードウェア仕様

**気象センサー:** 座標`35.5647N, 139.6544E` / Open-Meteo JMA / キャッシュ10分 / `weather_service.py`

**在宅確認センサー:** IP`192.168.0.30` / MAC`72:58:BA:C7:40:FA`(SHG07) / ARP/ICMP 2秒間隔・外出猶予30秒 / `presence_service.py`

**鍵トラッカー:** Tile UUID`0000feed-0000-1000-8000-00805f9b34fb` / `bluetoothctl`リアルタイムBLEスキャン(静的キャッシュ排除) / `tile_service.py`

**オートメーション:** `automation_service.py` / `automations_config.json`
- `平日6:30`: 日本の平日(土日祝除く) 06:30 リビング点灯
- `平日9:00`: 日本の平日 09:00 Eufy RoboVac G30起動 + Androidプッシュ通知
- `外出時`: 在宅→外出変化時、稼働機器(照明/エアコン/ヒーター)があれば通知。ボタン:「いってきます」「Novaへ指示」の2つのみ

**家電:**
- エアコン: SwitchBot API (冷房/除湿/オフ、22〜28℃)
- ヒーター: スマートプラグ/赤外線 (暖房/オフ、エコ、パワー)
- 照明: リモコンAPI (全灯、常夜灯、明るさ上下)
- クリーナー: Eufy RoboVac G30 (開始/一時停止/帰還/探す)
- デスクトップPC: IP `192.168.0.20` / MAC `a8:a1:59:60:6f:c0` / WoLブート / SSH電源制御
- 起動OS (USBスイッチ): Sinilink USB (ESPHome Native API, IP `192.168.0.210`:6053, Key `2653998163`) / ON=Bazzite, OFF=Windows / `pcTargetOs`二重永続化 ＆ PC電源オフ時の瞬断リセットに対するON自動復旧(セルフヒーリング)

**Nova Assist (Android):**
- パス: `android_bridge/` (Kotlin 1.9, Java 17, minSdk 26, targetSdk 34)
- 常駐: `NotificationService`(Foreground Service, `dataSync`属性, `BootReceiver`自動常駐)
- 通信: `HttpURLConnection` / `/api/notifications/stream` SSE + `/api/notifications/poll`フォールバック(外部ライブラリ依存ゼロ)
- **PWA通知は廃止・完全無効化。Nova Assistネイティブに一本化**
- 高機能通知: アクションボタン(`actions`) / インライン返信(`RemoteInput`) / プログレスバー(`progress`) / インプレース更新(`id`)
- Hardening(2026-09): `readTimeout=45000` / `last_poll_ts` SharedPreferences永続化 / `setOnlyAlertOnce(true)` / ID正規化(2000〜101999、常駐ID1001と衝突防止) / `getBaseUrl()`で`/dashboard`サブパス保持 / SSEキュー`maxsize=100`
- CLI: `smarthome notification [タイトル] <メッセージ>` / `smarthome notify <メッセージ> [--title, --progress, --action, --reply, --test-away, --test-progress]`
- テスト: `python3 test_notifications_e2e.py`(全8項目PASS)
- 自動ビルド: GitHub Actions `.github/workflows/build_apk.yml` → Release `android-latest` に `NovaAssist.apk`

**認証(クローラー遮断):**
- `auth_service.py`: `config.json`の`access_key`をHMAC-SHA256署名Cookie(`sh_auth`、10年、HttpOnly,Secure)で管理
- `serve.py`多層判定: 宅内LAN直接→無条件パス / `Tailscale-User-Login`ヘッダー→無条件パス / `sh_auth` Cookie→パス / `?key=<合言葉>`→Cookie発行+302リダイレクト / その他→403
- `NetworkUtils.kt`: `DEFAULT_ACCESS_KEY="Tamago1341"` / `X-Access-Key`ヘッダー常時送信 / CookieManager継承

**アイコン仕様:**
- 録音中: `graphic_eq`(Material Symbols Rounded、Android: `ic_graphic_eq.xml` 5本角丸波形バー `#fb7185`)
- 送信ボタン(入力中): `send`(Web) / `ic_send_custom.xml`(Android) / 色: bg`#1b222c`・枠`border-[#2196f3]/35`・アイコン`#60a5fa`
- 空欄/送信後: マイクボタンへ自動復帰

**PWAアイコン:** `icon.svg`/`icon-192.png`/`icon-512.png`/`icon-maskable-192.png`/`icon-maskable-512.png`/`apple-touch-icon.png` / `manifest.json`: `id`,`start_url`,`scope`=`/dashboard/` / `sw.js`: キャッシュ`v10`

## 3. 開発運用ルール

- `index.html`編集前: `cp index.html index.html.bak`
- 変更後: HTMLParser & JSブラケット整合性テスト (`python3 -m py_compile` 等の構文テスト)
- **【厳禁】実機状態の変更・強制オフの禁止:** テスト目的で実機（USBスイッチ、PC電源、照明、エアコン、ヒーター、クリーナー等）の電源をオフ・オン・変更しない。「いってきます」など全機器オフを伴う処理をテストで実行することは絶対禁止。テストは変更対象モジュールの構文・ロジック検証など必要最小限にとどめること。
- **【厳禁】通知テストの勝手な実行禁止:** `test_notifications_e2e.py` や `smarthome notify` などの通知テストは、ユーザーのスマホへ不要な通知が飛ぶため毎回のテストとして実行しない（ユーザーから明示的なテスト依頼があった場合のみ）。
- テスト通過後: `git commit & push` (`Soh-Hoshi/SmartHome-Dashboard`)
- 常駐: `systemctl --user restart dashboard.service`

## 4. 現在の稼働状態 (2026-09-08)

- `dashboard.service`: Active running, Port 8080
- `index.html`: 構文テストPASS / 送信ボタン切替・イコライザー波形連動
- APK: `android_bridge/app/build/outputs/apk/release/app-release.apk` v1.0.4 (2.5MB)
- Git: `origin/main` プッシュ可能状態
