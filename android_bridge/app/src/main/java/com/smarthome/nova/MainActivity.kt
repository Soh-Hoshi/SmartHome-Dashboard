package com.smarthome.nova

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.os.Build
import android.os.Bundle
import android.webkit.PermissionRequest
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

@SuppressLint("NewApi")
class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private val PERMISSION_REQUEST_CODE = 101

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {

        super.onCreate(savedInstanceState)

        window.statusBarColor = Color.parseColor("#0d0f12")
        window.navigationBarColor = Color.parseColor("#0d0f12")

        webView = WebView(this).apply {
            setBackgroundColor(Color.parseColor("#0d0f12"))
            settings.apply {
                javaScriptEnabled = true
                domStorageEnabled = true
                databaseEnabled = true
                cacheMode = WebSettings.LOAD_DEFAULT
                mediaPlaybackRequiresUserGesture = false
                allowFileAccess = true
                allowContentAccess = true
            }

            webChromeClient = object : WebChromeClient() {
                override fun onPermissionRequest(request: PermissionRequest?) {
                    request?.grant(request.resources)
                }
            }
            webViewClient = object : WebViewClient() {
                override fun onPageFinished(view: WebView?, url: String?) {
                    super.onPageFinished(view, url)
                    android.webkit.CookieManager.getInstance().flush()
                }
            }
        }

        android.webkit.CookieManager.getInstance().apply {
            setAcceptCookie(true)
            setAcceptThirdPartyCookies(webView, true)
        }

        setContentView(webView)

        // パーミッション要求（マイク & 通知）
        checkRequiredPermissions()

        // バックグラウンド通知常駐サービスの開始
        NotificationService.start(this)

        val sharedPref = getSharedPreferences("com.smarthome.nova_preferences", Context.MODE_PRIVATE)
        if (!sharedPref.contains("access_key")) {
            sharedPref.edit().putString("access_key", NetworkUtils.DEFAULT_ACCESS_KEY).apply()
        }

        val defaultUrl = "https://home.sohhoshi.com"
        var url = sharedPref.getString("dashboard_url", defaultUrl) ?: defaultUrl
        if (url.contains("tail52d127.ts.net")) {
            url = defaultUrl
            sharedPref.edit().putString("dashboard_url", defaultUrl).apply()
        }

        val targetUrl = intent?.getStringExtra("TARGET_URL") ?: url
        saveKeyFromUrlIfPresent(targetUrl)

        val finalUrl = try {
            val cookie = android.webkit.CookieManager.getInstance().getCookie(targetUrl)
            val key = sharedPref.getString("access_key", NetworkUtils.DEFAULT_ACCESS_KEY) ?: NetworkUtils.DEFAULT_ACCESS_KEY
            if ((cookie.isNullOrEmpty() || !cookie.contains("sh_auth")) && !targetUrl.contains("key=")) {
                val sep = if (targetUrl.contains("?")) "&" else "?"
                "$targetUrl${sep}key=$key"
            } else {
                targetUrl
            }
        } catch (e: Exception) {
            targetUrl
        }

        webView.loadUrl(finalUrl)
    }

    override fun onNewIntent(intent: Intent?) {
        super.onNewIntent(intent)
        setIntent(intent)
        val targetUrl = intent?.getStringExtra("TARGET_URL")
        if (!targetUrl.isNullOrEmpty()) {
            saveKeyFromUrlIfPresent(targetUrl)
            webView.loadUrl(targetUrl)
        }
    }

    private fun saveKeyFromUrlIfPresent(targetUrl: String) {
        try {
            val u = java.net.URL(targetUrl)
            val query = u.query
            if (!query.isNullOrEmpty()) {
                for (param in query.split("&")) {
                    val parts = param.split("=")
                    if (parts.size == 2 && parts[0] == "key") {
                        val sharedPref = getSharedPreferences("com.smarthome.nova_preferences", Context.MODE_PRIVATE)
                        sharedPref.edit().putString("access_key", parts[1]).apply()
                        break
                    }
                }
            }
        } catch (ignored: Exception) {}
    }

    private fun checkRequiredPermissions() {
        val permissions = mutableListOf<String>()

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
            != PackageManager.PERMISSION_GRANTED
        ) {
            permissions.add(Manifest.permission.RECORD_AUDIO)
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED
            ) {
                permissions.add(Manifest.permission.POST_NOTIFICATIONS)
            }
        }

        if (permissions.isNotEmpty()) {
            ActivityCompat.requestPermissions(
                this,
                permissions.toTypedArray(),
                PERMISSION_REQUEST_CODE
            )
        }
    }
}

