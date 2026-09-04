package com.smarthome.nova

import android.app.NotificationManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.app.RemoteInput
import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

class NotificationActionReceiver : BroadcastReceiver() {

    companion object {
        private const val TAG = "NotificationActionReceiver"
        const val ACTION_NOTIFICATION_CLICK = "com.smarthome.nova.ACTION_NOTIFICATION_CLICK"
        const val KEY_TEXT_REPLY = "key_text_reply"

        const val EXTRA_NOTIF_ID = "extra_notif_id"
        const val EXTRA_COMMAND = "extra_command"
        const val EXTRA_DISMISS = "extra_dismiss"
        const val EXTRA_TITLE = "extra_title"
    }

    override fun onReceive(context: Context, intent: Intent) {
        val notifId = intent.getIntExtra(EXTRA_NOTIF_ID, 0)
        val isDismiss = intent.getBooleanExtra(EXTRA_DISMISS, false)
        val notifTitle = intent.getStringExtra(EXTRA_TITLE) ?: "SmartHome"

        if (isDismiss) {
            val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as? NotificationManager
            manager?.cancel(notifId)
            Log.d(TAG, "Notification dismissed: $notifId")
            return
        }

        // Direct Reply のテキスト入力があるか確認
        val remoteInput = RemoteInput.getResultsFromIntent(intent)
        val replyText = remoteInput?.getCharSequence(KEY_TEXT_REPLY)?.toString()

        // 実行するコマンド（Direct Reply入力 または アクションボタンの固定command）
        val command = replyText ?: intent.getStringExtra(EXTRA_COMMAND) ?: ""
        if (command.isBlank()) return

        Log.i(TAG, "Processing notification action: command='$command', notifId=$notifId")

        // 1. 即時インプレース更新: 「⏳ 実行中...」を通知バーに表示
        updateNotificationInProgress(context, notifId, notifTitle, command)

        // 2. 非同期スレッドでサーバー API (/api/assistant) をバックグラウンド実行
        val pendingResult = goAsync()
        thread {
            try {
                val baseUrl = getBaseUrl(context)
                val responseMsg = executeAssistantCommand(baseUrl, command)

                // 3. インプレース完了更新: サーバー応答を既存通知にその場で反映
                updateNotificationCompleted(context, notifId, notifTitle, responseMsg)
            } catch (e: Exception) {
                Log.e(TAG, "Error executing action command: ${e.message}", e)
                updateNotificationError(context, notifId, notifTitle, "エラーが発生しました: ${e.message}")
            } finally {
                pendingResult.finish()
            }
        }
    }

    private fun updateNotificationInProgress(context: Context, notifId: Int, title: String, command: String) {
        val notification = NotificationCompat.Builder(context, NotificationService.CHANNEL_ALERT_ID)
            .setSmallIcon(R.drawable.ic_nova_foreground)
            .setContentTitle(title)
            .setContentText("⏳ 実行中: $command")
            .setProgress(0, 0, true)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .build()

        NotificationManagerCompat.from(context).notify(notifId, notification)
    }

    private fun updateNotificationCompleted(context: Context, notifId: Int, title: String, responseMsg: String) {
        val notification = NotificationCompat.Builder(context, NotificationService.CHANNEL_ALERT_ID)
            .setSmallIcon(R.drawable.ic_nova_foreground)
            .setContentTitle("✅ 実行完了")
            .setContentText(responseMsg)
            .setStyle(NotificationCompat.BigTextStyle().bigText(responseMsg))
            .setProgress(0, 0, false)
            .setOngoing(false)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .build()

        NotificationManagerCompat.from(context).notify(notifId, notification)
    }

    private fun updateNotificationError(context: Context, notifId: Int, title: String, errorMsg: String) {
        val notification = NotificationCompat.Builder(context, NotificationService.CHANNEL_ALERT_ID)
            .setSmallIcon(R.drawable.ic_nova_foreground)
            .setContentTitle("⚠️ エラー")
            .setContentText(errorMsg)
            .setProgress(0, 0, false)
            .setOngoing(false)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .build()

        NotificationManagerCompat.from(context).notify(notifId, notification)
    }

    private fun executeAssistantCommand(baseUrl: String, prompt: String): String {
        val url = URL("$baseUrl/api/assistant")
        val conn = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            setRequestProperty("Content-Type", "application/json; charset=UTF-8")
            connectTimeout = 10000
            readTimeout = 15000
            doOutput = true
        }

        val jsonBody = JSONObject().apply {
            put("prompt", prompt)
        }

        OutputStreamWriter(conn.outputStream, "UTF-8").use {
            it.write(jsonBody.toString())
            it.flush()
        }

        val code = conn.responseCode
        if (code in 200..299) {
            val respStr = conn.inputStream.bufferedReader().readText()
            val respJson = JSONObject(respStr)
            return respJson.optString("message", "操作を完了しました。")
        } else {
            val errStr = conn.errorStream?.bufferedReader()?.readText() ?: ""
            throw RuntimeException("HTTP $code: $errStr")
        }
    }

    private fun getBaseUrl(context: Context): String {
        val sharedPref = context.getSharedPreferences("com.smarthome.nova_preferences", Context.MODE_PRIVATE)
        val defaultUrl = "https://server.tail52d127.ts.net/dashboard"
        val fullUrl = sharedPref.getString("dashboard_url", defaultUrl) ?: defaultUrl

        return try {
            val u = URL(fullUrl)
            val portStr = if (u.port != -1) ":${u.port}" else ""
            "${u.protocol}://${u.host}$portStr"
        } catch (e: Exception) {
            "https://server.tail52d127.ts.net"
        }
    }
}
