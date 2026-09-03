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
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.atomic.AtomicBoolean

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
            lastPollTimestamp = System.currentTimeMillis() / 1000.0 - 5.0

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
                        readTimeout = 0 // 無限タイムアウトでSSE待機
                        instanceFollowRedirects = true
                    }

                    val code = connection.responseCode
                    if (code in 200..299) {
                        Log.i(TAG, "Connected to SSE stream successfully")
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
                            showHeadsUpNotification(
                                notifObj.optString("title", "SmartHome"),
                                notifObj.optString("message", notifObj.optString("body", ""))
                            )
                        }
                    }
                    val serverTime = json.optDouble("server_time", 0.0)
                    if (serverTime > lastPollTimestamp) {
                        lastPollTimestamp = serverTime
                    }
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
            val title = obj.optString("title", "SmartHome")
            val message = obj.optString("message", obj.optString("body", ""))
            val ts = obj.optDouble("timestamp", 0.0)
            if (ts > lastPollTimestamp) {
                lastPollTimestamp = ts
            }
            if (message.isNotEmpty() || title.isNotEmpty()) {
                showHeadsUpNotification(title, message)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error parsing notification JSON: $jsonStr", e)
        }
    }

    private fun showHeadsUpNotification(title: String, message: String) {
        val notifId = (System.currentTimeMillis() % 100000).toInt() + 2000

        val openIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            this,
            notifId,
            openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(this, CHANNEL_ALERT_ID)
            .setSmallIcon(R.drawable.ic_nova_foreground)
            .setContentTitle(title)
            .setContentText(message)
            .setStyle(NotificationCompat.BigTextStyle().bigText(message))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setDefaults(NotificationCompat.DEFAULT_ALL)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .build()

        try {
            NotificationManagerCompat.from(this).notify(notifId, notification)
            Log.i(TAG, "Heads-up notification posted: $title - $message")
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
            "${u.protocol}://${u.host}$portStr"
        } catch (e: Exception) {
            "https://server.tail52d127.ts.net"
        }
    }

    override fun onDestroy() {
        isRunning.set(false)
        workerThread?.interrupt()
        super.onDestroy()
    }
}





