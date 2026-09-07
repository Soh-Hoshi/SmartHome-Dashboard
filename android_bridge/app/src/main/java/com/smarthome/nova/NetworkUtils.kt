package com.smarthome.nova

import android.content.Context
import android.webkit.CookieManager
import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

object NetworkUtils {

    fun getBaseUrl(context: Context): String {
        val sharedPref = context.getSharedPreferences("com.smarthome.nova_preferences", Context.MODE_PRIVATE)
        val defaultUrl = "https://home.sohhoshi.com/?key=uFD3nti9jGViEBwm4zceAQ"
        var fullUrl = sharedPref.getString("dashboard_url", defaultUrl) ?: defaultUrl
        if (fullUrl.contains("tail52d127.ts.net")) {
            fullUrl = defaultUrl
        }

        return try {
            val u = URL(fullUrl)
            val portStr = if (u.port != -1) ":${u.port}" else ""
            val path = u.path.trimEnd('/')
            "${u.protocol}://${u.host}$portStr$path"
        } catch (e: Exception) {
            "https://home.sohhoshi.com"
        }
    }

    fun applyAuthHeaders(conn: HttpURLConnection, baseUrl: String, context: Context) {
        // 1. WebView CookieManager からセッション Cookie を引き継ぐ
        try {
            val cookie = CookieManager.getInstance().getCookie(baseUrl)
            if (!cookie.isNullOrEmpty()) {
                conn.setRequestProperty("Cookie", cookie)
            }
        } catch (ignored: Exception) {}

        // 2. 設定 URL に ?key=... が含まれている場合は X-Access-Key ヘッダーとしても付与
        try {
            val sharedPref = context.getSharedPreferences("com.smarthome.nova_preferences", Context.MODE_PRIVATE)
            val defaultUrl = "https://home.sohhoshi.com/?key=uFD3nti9jGViEBwm4zceAQ"
            var fullUrl = sharedPref.getString("dashboard_url", defaultUrl) ?: defaultUrl
            if (fullUrl.contains("tail52d127.ts.net")) {
                fullUrl = defaultUrl
            }
            val u = URL(fullUrl)
            val query = u.query
            if (!query.isNullOrEmpty()) {
                for (param in query.split("&")) {
                    val parts = param.split("=")
                    if (parts.size == 2 && parts[0] == "key") {
                        conn.setRequestProperty("X-Access-Key", parts[1])
                        break
                    }
                }
            }
        } catch (ignored: Exception) {}
    }

    fun executeAssistantCommand(context: Context, prompt: String): Pair<Boolean, String> {
        return try {
            val baseUrl = getBaseUrl(context)
            val url = URL("$baseUrl/api/assistant")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                setRequestProperty("Content-Type", "application/json; charset=UTF-8")
                connectTimeout = 10000
                readTimeout = 15000
                doOutput = true
                applyAuthHeaders(this, baseUrl, context)
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
                val success = respJson.optBoolean("success", true)
                val msg = respJson.optString("message", "操作を完了しました。")
                Pair(success, msg)
            } else {
                Pair(false, "通信エラーが発生しました (HTTP $code)")
            }
        } catch (e: Exception) {
            Pair(false, "接続に失敗しました: ${e.message ?: "タイムアウト"}")
        }
    }
}
