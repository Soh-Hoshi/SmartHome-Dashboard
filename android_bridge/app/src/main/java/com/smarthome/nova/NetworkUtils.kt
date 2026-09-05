package com.smarthome.nova

import android.content.Context
import android.webkit.CookieManager
import java.net.HttpURLConnection
import java.net.URL

object NetworkUtils {

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
            val defaultUrl = "https://server.tail52d127.ts.net/dashboard"
            val fullUrl = sharedPref.getString("dashboard_url", defaultUrl) ?: defaultUrl
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
}
