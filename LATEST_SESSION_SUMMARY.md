# SmartHome Dashboard - セッション引き継ぎ (2026-09-08)

詳細仕様: [`PROJECT_MEMORY.md`](file:///home/soh/dashboard/PROJECT_MEMORY.md)

## 直近の変更 (2026-09-04〜08)

1. **Android通知Hardening**: `onNewIntent`実装 / SSE空通知抑止(server_time同期) / `readTimeout=45000` / `last_poll_ts`永続化 / `setOnlyAlertOnce` / ID正規化(2000〜101999) / `/dashboard`サブパス保持 / `contentIntent`+`SecurityException`保護 / SSEキュー`maxsize=100` / LiveReload keepalive 20秒 / E2Eテスト全8項目PASS
2. **オートメーション追加**: `weekday_morning_cleaner`(平日09:00 JST、Eufy RoboVac G30起動+通知) を`automations_config.json`に登録
3. **外出時通知簡素化**: 全機器OFF時は通知スキップ / 本文・絵文字・機器名全廃 / ボタン:「いってきます」「Novaへ指示」の2つのみ / タイトル:「お出かけですか？」
4. **名称統一**: 掃除機→「クリーナー」/ ライト→「リビング照明」(`automation_service.py`, `assistant_engine.py`, `smarthome` CLI)
5. **シーン応答文短縮**: 「挨拶\n短い実行結果」形式。例:「いってらっしゃい！\n照明と空調を停止しました。」
6. **クローラー遮断**: HMAC Cookie(`sh_auth`) + `DEFAULT_ACCESS_KEY="Tamago1341"` / 宅内LAN・Tailscale VPNは無条件パス / 外部クローラー→403
7. **PWAアイコン整備**: `icon-maskable-*.png`追加 / `manifest.json` `id`/`scope`=`/dashboard/` / `sw.js` v10
8. **Nova Assist v1.0.4 (2026-09-08)**: HTTP 403解消(`X-Access-Key`常時送信) / 録音アイコン→`graphic_eq`(波形`#fb7185`) / 送信ボタン→`send`アイコン(`#1b222c`+`#60a5fa`) / `AssistActivity.kt`で入力中/通常/録音中の3状態をダッシュボードと1:1同期

## 稼働状態

| 項目 | 状態 |
| :--- | :--- |
| `dashboard.service` | Active running, Port 8080 |
| APK Release | v1.0.4 (2.5MB) `android_bridge/.../apk/release/app-release.apk` |
| Git | `origin/main` プッシュ可能 |

## クイックコマンド

```bash
systemctl --user status dashboard.service
python3 /home/soh/dashboard/test_notifications_e2e.py
/home/soh/dashboard/smarthome notify --test-away
/home/soh/dashboard/smarthome cleaner start
```
