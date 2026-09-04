package com.smarthome.nova

import android.annotation.SuppressLint
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.graphics.Color
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.app.RemoteInput
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.atomic.AtomicBoolean
import kotlin.math.abs

@SuppressLint("MissingPermission", "NewApi", "InlinedApi")
class NotificationService : Service() {


    companion object {
        private const val TAG = "NovaNotificationService"
        const val CHANNEL_SERVICE_ID = "nova_service_channel"
        const val CHANNEL_ALERT_ID = "nova_alert_channel"
        private const val NOTIFICATION_SERVICE_ID = 1001

        fun start(context: Context) {
            val intent = Intent(context, NotificationService::class.java)
            try {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    context.startForegroundService(intent)
                } else {
                    context.startService(intent)
                }
            } catch (e: Exception) {
                Log.e(TAG, "Failed to start NotificationService", e)
            }
        }
    }

    private val isRunning = AtomicBoolean(false)
    private var workerThread: Thread? = null
    private var lastPollTimestamp: Double = 0.0

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannels()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val foregroundNotification = buildForegroundNotification()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(
                NOTIFICATION_SERVICE_ID,
                foregroundNotification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC
            )
        } else {
            startForeground(NOTIFICATION_SERVICE_ID, foregroundNotification)
        }

        if (!isRunning.getAndSet(true)) {
            startWorker()
        }

        return START_STICKY
    }

    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val manager = getSystemService(NotificationManager::class.java) ?: return

            // 常駐通知チャンネル (低優先度・サイレント)
            val serviceChannel = NotificationChannel(
                CHANNEL_SERVICE_ID,
                getString(R.string.service_channel_name),
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = getString(R.string.service_channel_desc)
                setShowBadge(false)
            }
            manager.createNotificationChannel(serviceChannel)

            // アラート通知チャンネル (高優先度・ヘッドアップ・音・バイブあり)
            val alertChannel = NotificationChannel(
                CHANNEL_ALERT_ID,
                getString(R.string.alert_channel_name),
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = getString(R.string.alert_channel_desc)
                enableLights(true)
                lightColor = Color.BLUE
                enableVibration(true)
                vibrationPattern = longArrayOf(0, 250, 100, 250)
                setShowBadge(true)
                lockscreenVisibility = Notification.VISIBILITY_PUBLIC
            }
            manager.createNotificationChannel(alertChannel)
        }
    }

    private fun buildForegroundNotification(): Notification {
        val openIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, CHANNEL_SERVICE_ID)
            .setContentTitle(getString(R.string.app_name))
            .setContentText(getString(R.string.service_running_text))
            .setSmallIcon(R.drawable.ic_nova_foreground)
            .setContentIntent(pendingIntent)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .build()
    }

    private fun startWorker() {
        workerThread = Thread {
            Log.i(TAG, "Notification worker thread started")
            val prefs = getSharedPreferences("com.smarthome.nova_preferences", Context.MODE_PRIVATE)
            val savedTs = prefs.getFloat("last_poll_ts", 0f).toDouble()
            lastPollTimestamp = if (savedTs > 0) savedTs else (System.currentTimeMillis() / 1000.0 - 5.0)

            while (isRunning.get()) {
                val baseUrl = getBaseUrl()
                val streamUrl = "$baseUrl/api/notifications/stream"

                var connection: HttpURLConnection? = null
                var reader: BufferedReader? = null
                try {
                    Log.d(TAG, "Connecting to SSE stream: $streamUrl")
                    val url = URL(streamUrl)
                    connection = (url.openConnection() as HttpURLConnection).apply {
                        requestMethod = "GET"
                        setRequestProperty("Accept", "text/event-stream")
                        setRequestProperty("Cache-Control", "no-cache")
                        connectTimeout = 15000
                        readTimeout = 45000 // 45秒タイムアウト（サーバー側15秒keepaliveで切断を早期検知）
                        instanceFollowRedirects = true
                    }

                    val code = connection.responseCode
                    if (code in 200..299) {
                        Log.i(TAG, "Connected to SSE stream successfully")
                        try { pollFallback(baseUrl) } catch (e: Exception) { Log.w(TAG, "Catch-up poll failed: ${e.message}") }
                        reader = BufferedReader(InputStreamReader(connection.inputStream, "UTF-8"))
                        while (isRunning.get()) {
                            val line = reader?.readLine() ?: break
                            val l = line.trim()

                            if (l.startsWith("data:")) {
                                val dataStr = l.substring(5).trim()
                                if (dataStr.isNotEmpty() && dataStr.startsWith("{")) {
                                    handleNotificationJson(dataStr)
                                }
                            }
                        }

                    } else {
                        Log.w(TAG, "SSE returned non-200 status: $code")
                        pollFallback(baseUrl)
                        Thread.sleep(10000)
                    }
                } catch (e: Exception) {
                    Log.w(TAG, "SSE connection error/disconnected: ${e.message}")
                    try {
                        pollFallback(baseUrl)
                    } catch (ignored: Exception) {}
                    try {
                        Thread.sleep(5000)
                    } catch (ignored: InterruptedException) {
                        break
                    }
                } finally {
                    try { reader?.close() } catch (ignored: Exception) {}
                    try { connection?.disconnect() } catch (ignored: Exception) {}
                }
            }

            Log.i(TAG, "Notification worker thread terminated")
        }.apply {
            name = "NovaNotificationWorker"
            isDaemon = true
            start()
        }
    }

    private fun pollFallback(baseUrl: String) {
        val pollUrl = "$baseUrl/api/notifications/poll?since=$lastPollTimestamp"
        var conn: HttpURLConnection? = null
        try {
            val url = URL(pollUrl)
            conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = 8000
                readTimeout = 8000
            }
            if (conn.responseCode == 200) {
                val response = conn.inputStream.bufferedReader().readText()
                val json = JSONObject(response)
                if (json.optString("status") == "success") {
                    val notifs = json.optJSONArray("notifications")
                    if (notifs != null) {
                        for (i in 0 until notifs.length()) {
                            val notifObj = notifs.getJSONObject(i)
                            val ts = notifObj.optDouble("timestamp", 0.0)
                            if (ts > lastPollTimestamp) {
                                lastPollTimestamp = ts
                            }
                            showNotification(notifObj)
                        }
                    }
                    val serverTime = json.optDouble("server_time", 0.0)
                    if (serverTime > lastPollTimestamp) {
                        lastPollTimestamp = serverTime
                    }
                    getSharedPreferences("com.smarthome.nova_preferences", Context.MODE_PRIVATE)
                        .edit().putFloat("last_poll_ts", lastPollTimestamp.toFloat()).apply()
                }
            }
        } catch (e: Exception) {
            Log.w(TAG, "Poll fallback failed: ${e.message}")
        } finally {
            try { conn?.disconnect() } catch (ignored: Exception) {}
        }
    }

    private fun handleNotificationJson(jsonStr: String) {
        try {
            val obj = JSONObject(jsonStr)
            if (obj.optString("status") == "connected") {
                val serverTime = obj.optDouble("server_time", 0.0)
                if (serverTime > 0) {
                    if (lastPollTimestamp <= 0) {
                        lastPollTimestamp = serverTime - 5.0
                    }
                    getSharedPreferences("com.smarthome.nova_preferences", Context.MODE_PRIVATE)
                        .edit().putFloat("last_poll_ts", lastPollTimestamp.toFloat()).apply()
                }
                return
            }

            val message = obj.optString("message", obj.optString("body", "")).trim()
            if (message.isEmpty() && !obj.has("progress")) {
                return
            }

            val ts = obj.optDouble("timestamp", 0.0)
            if (ts > lastPollTimestamp) {
                lastPollTimestamp = ts
                getSharedPreferences("com.smarthome.nova_preferences", Context.MODE_PRIVATE)
                    .edit().putFloat("last_poll_ts", ts.toFloat()).apply()
            }
            showNotification(obj)
        } catch (e: Exception) {
            Log.e(TAG, "Error parsing notification JSON: $jsonStr", e)
        }
    }

    private fun showNotification(obj: JSONObject) {
        val title = obj.optString("title", "SmartHome")
        val message = obj.optString("message", obj.optString("body", ""))

        // notifId: 指定があれば数値またはハッシュから安定した正の安全なIDを生成（インプレース更新に対応、ID 1001の前景サービスとの衝突を回避）
        val rawId = obj.opt("id")
        val notifId = when (rawId) {
            is Number -> ((rawId.toLong() and 0x7fffffffL) % 100000 + 2000).toInt()
            is String -> if (rawId.isNotEmpty()) (rawId.hashCode() and 0x7fffffff) % 100000 + 2000 else (System.currentTimeMillis() % 100000).toInt() + 2000
            else -> (System.currentTimeMillis() % 100000).toInt() + 2000
        }

        val openIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            val targetPath = obj.optJSONObject("data")?.optString("url", "") ?: ""
            if (targetPath.isNotEmpty()) {
                val fullTarget = if (targetPath.startsWith("http")) targetPath else "${getBaseUrl()}$targetPath"
                putExtra("TARGET_URL", fullTarget)
            }
        }
        val pendingIntent = PendingIntent.getActivity(
            this,
            notifId,
            openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val ongoing = obj.optBoolean("ongoing", false)
        val autoCancel = obj.optBoolean("auto_cancel", !ongoing)
        val priorityStr = obj.optString("priority", "high")
        val priorityVal = when (priorityStr.lowercase()) {
            "low" -> NotificationCompat.PRIORITY_LOW
            "default" -> NotificationCompat.PRIORITY_DEFAULT
            else -> NotificationCompat.PRIORITY_HIGH
        }

        val builder = NotificationCompat.Builder(this, CHANNEL_ALERT_ID)
            .setSmallIcon(R.drawable.ic_nova_foreground)
            .setContentTitle(title)
            .setContentText(message)
            .setPriority(priorityVal)
            .setDefaults(NotificationCompat.DEFAULT_ALL)
            .setOnlyAlertOnce(true)
            .setOngoing(ongoing)
            .setAutoCancel(autoCancel)
            .setContentIntent(pendingIntent)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)

        // 1. プログレスバー機能 (プログレスバー設定時は BigTextStyle を適用しない)
        val progressObj = obj.optJSONObject("progress")
        if (progressObj != null) {
            val max = progressObj.optInt("max", 100)
            val current = progressObj.optInt("current", 0)
            val indeterminate = progressObj.optBoolean("indeterminate", false)
            builder.setProgress(max, current, indeterminate)
        } else {
            builder.setStyle(NotificationCompat.BigTextStyle().bigText(message))
        }

        // 2. アクションボタン ＆ インライン返信 (Direct Reply) 機能
        val actionsArray = obj.optJSONArray("actions")
        if (actionsArray != null && actionsArray.length() > 0) {
            val flagMutable = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_MUTABLE
            } else {
                PendingIntent.FLAG_UPDATE_CURRENT
            }

            for (i in 0 until actionsArray.length()) {
                val actionObj = actionsArray.getJSONObject(i)
                val actionTitle = actionObj.optString("title", "")
                val command = actionObj.optString("command", "")
                val isDismiss = actionObj.optBoolean("dismiss", false)
                val isReply = actionObj.optBoolean("reply", false)
                val replyPlaceholder = actionObj.optString("reply_placeholder", "Novaに指示...")

                val actionIntent = Intent(this, NotificationActionReceiver::class.java).apply {
                    action = NotificationActionReceiver.ACTION_NOTIFICATION_CLICK
                    putExtra(NotificationActionReceiver.EXTRA_NOTIF_ID, notifId)
                    putExtra(NotificationActionReceiver.EXTRA_COMMAND, command)
                    putExtra(NotificationActionReceiver.EXTRA_DISMISS, isDismiss)
                    putExtra(NotificationActionReceiver.EXTRA_TITLE, title)
                }

                val requestCode = notifId * 10 + i
                val actionPendingIntent = PendingIntent.getBroadcast(
                    this,
                    requestCode,
                    actionIntent,
                    flagMutable
                )

                val actionIcon = actionObj.optInt("icon", 0)
                val actionBuilder = NotificationCompat.Action.Builder(
                    actionIcon,
                    actionTitle,
                    actionPendingIntent
                ).setAllowGeneratedReplies(true)

                if (isReply) {
                    val remoteInput = RemoteInput.Builder(NotificationActionReceiver.KEY_TEXT_REPLY)
                        .setLabel(replyPlaceholder)
                        .build()
                    actionBuilder.addRemoteInput(remoteInput)
                }

                builder.addAction(actionBuilder.build())
            }
        }

        try {
            NotificationManagerCompat.from(this).notify(notifId, builder.build())
            Log.i(TAG, "Notification posted: id=$notifId, title='$title', message='$message'")
        } catch (e: SecurityException) {
            Log.w(TAG, "Permission POST_NOTIFICATIONS missing or denied", e)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to display notification", e)
        }
    }

    private fun getBaseUrl(): String {
        val sharedPref = getSharedPreferences("com.smarthome.nova_preferences", Context.MODE_PRIVATE)
        val defaultUrl = "https://server.tail52d127.ts.net/dashboard"
        val fullUrl = sharedPref.getString("dashboard_url", defaultUrl) ?: defaultUrl

        return try {
            val u = URL(fullUrl)
            val portStr = if (u.port != -1) ":${u.port}" else ""
            val path = u.path.trimEnd('/')
            "${u.protocol}://${u.host}$portStr$path"
        } catch (e: Exception) {
            "https://server.tail52d127.ts.net/dashboard"
        }
    }

    override fun onDestroy() {
        isRunning.set(false)
        workerThread?.interrupt()
        super.onDestroy()
    }
}





