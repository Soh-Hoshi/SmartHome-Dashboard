package com.smarthome.nova

import android.content.Context
import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity

class AssistActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // デフォルトURLに ?assist=1 を付加してMainActivityを起動
        val sharedPref = getSharedPreferences("com.smarthome.nova_preferences", Context.MODE_PRIVATE)
        val baseUrl = sharedPref.getString("dashboard_url", getString(R.string.default_dashboard_url))
            ?: getString(R.string.default_dashboard_url)

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
