package com.smarthome.nova

import android.content.Context
import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity

class AssistActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val defaultUrl = "https://server.tail52d127.ts.net/dashboard"
        val sharedPref = getSharedPreferences("com.smarthome.nova_preferences", Context.MODE_PRIVATE)
        val baseUrl = sharedPref.getString("dashboard_url", defaultUrl) ?: defaultUrl

        val assistUrl = if (baseUrl.contains("?")) {
            "$baseUrl&assist=1"
        } else {
            "$baseUrl?assist=1"
        }

        val intent = Intent(this, MainActivity::class.java).apply {
            putExtra("TARGET_URL", assistUrl)
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }

        startActivity(intent)
        finish()
    }
}
