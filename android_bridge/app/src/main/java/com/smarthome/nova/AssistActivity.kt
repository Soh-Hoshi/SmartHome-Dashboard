package com.smarthome.nova

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.text.Editable
import android.text.TextWatcher
import android.view.GestureDetector
import android.view.MotionEvent
import android.view.View
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import android.widget.EditText
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

class AssistActivity : AppCompatActivity() {

    private val PERMISSION_REQUEST_RECORD_AUDIO = 201
    private val mainHandler = Handler(Looper.getMainLooper())
    private var autoDismissRunnable: Runnable? = null

    private lateinit var rootLayout: FrameLayout
    private lateinit var floatingContainer: LinearLayout
    private lateinit var btnOpenDashboard: LinearLayout
    private lateinit var statusContainer: LinearLayout
    private lateinit var tvStatus: TextView
    private lateinit var loadingSpinner: ProgressBar
    private lateinit var searchPill: LinearLayout
    private lateinit var etCommand: EditText
    private lateinit var btnAction: FrameLayout
    private lateinit var iconAction: ImageView

    private var speechRecognizer: SpeechRecognizer? = null
    private var isListening = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_assist_overlay)

        initViews()
        setupListeners()
        setupGestures()

        checkAudioPermissionAndStartListening()
    }

    private fun initViews() {
        rootLayout = findViewById(R.id.rootLayout)
        floatingContainer = findViewById(R.id.floatingContainer)
        btnOpenDashboard = findViewById(R.id.btnOpenDashboard)
        statusContainer = findViewById(R.id.statusContainer)
        tvStatus = findViewById(R.id.tvStatus)
        loadingSpinner = findViewById(R.id.loadingSpinner)
        searchPill = findViewById(R.id.searchPill)
        etCommand = findViewById(R.id.etCommand)
        btnAction = findViewById(R.id.btnAction)
        iconAction = findViewById(R.id.iconAction)
    }

    private fun setupListeners() {
        // 外側タップで終了
        rootLayout.setOnClickListener {
            dismissWithAnimation()
        }

        // 検索カプセル自体のタップはイベント消費
        searchPill.setOnClickListener {
            cancelAutoDismiss()
        }

        // ダッシュボードを開く小さなフロートボタン
        btnOpenDashboard.setOnClickListener {
            openDashboard()
        }

        // 入力監視 (文字あり: 送信 / 文字なし: マイク)
        etCommand.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                cancelAutoDismiss()
                updateActionButtonUi()
            }
            override fun afterTextChanged(s: Editable?) {}
        })

        // キーボードのEnter/送信
        etCommand.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_SEND || actionId == EditorInfo.IME_ACTION_DONE) {
                val text = etCommand.text.toString().trim()
                if (text.isNotEmpty()) {
                    hideKeyboard()
                    submitCommand(text)
                }
                true
            } else {
                false
            }
        }

        // アクションボタン (マイク / 送信)
        btnAction.setOnClickListener {
            cancelAutoDismiss()
            val text = etCommand.text.toString().trim()
            if (text.isNotEmpty()) {
                hideKeyboard()
                submitCommand(text)
            } else {
                if (isListening) {
                    stopListening()
                } else {
                    startListening()
                }
            }
        }
    }

    private fun setupGestures() {
        val gestureDetector = GestureDetector(this, object : GestureDetector.SimpleOnGestureListener() {
            override fun onFling(e1: MotionEvent?, e2: MotionEvent, velocityX: Float, velocityY: Float): Boolean {
                if (e1 == null) return false
                val dy = e2.rawY - e1.rawY
                if (dy > 80 && Math.abs(velocityY) > 200) {
                    // 下フリックで閉じる
                    dismissWithAnimation()
                    return true
                } else if (dy < -80 && Math.abs(velocityY) > 200) {
                    // 上フリックでダッシュボード
                    openDashboard()
                    return true
                }
                return false
            }
        })

        searchPill.setOnTouchListener { _, event ->
            gestureDetector.onTouchEvent(event)
            false
        }
    }

    private fun checkAudioPermissionAndStartListening() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
            != PackageManager.PERMISSION_GRANTED
        ) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.RECORD_AUDIO),
                PERMISSION_REQUEST_RECORD_AUDIO
            )
        } else {
            startListening()
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERMISSION_REQUEST_RECORD_AUDIO) {
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                startListening()
            } else {
                etCommand.hint = "テキストで入力してください"
                etCommand.requestFocus()
            }
        }
    }

    private fun startListening() {
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            etCommand.hint = "キーボードで入力してください"
            return
        }

        try {
            speechRecognizer?.destroy()
            speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this).apply {
                setRecognitionListener(object : RecognitionListener {
                    override fun onReadyForSpeech(params: Bundle?) {
                        isListening = true
                        updateActionButtonUi()
                        etCommand.hint = "お聞きしています..."
                    }

                    override fun onBeginningOfSpeech() {
                        statusContainer.visibility = View.VISIBLE
                        loadingSpinner.visibility = View.GONE
                        tvStatus.text = "音声を認識中..."
                    }

                    override fun onRmsChanged(rmsdB: Float) {
                        if (isListening) {
                            val scale = 1.0f + (Math.max(0f, rmsdB) / 10f) * 0.25f
                            btnAction.animate().scaleX(scale).scaleY(scale).setDuration(80).start()
                        }
                    }

                    override fun onBufferReceived(buffer: ByteArray?) {}

                    override fun onEndOfSpeech() {
                        isListening = false
                        resetMicScale()
                        updateActionButtonUi()
                        statusContainer.visibility = View.VISIBLE
                        loadingSpinner.visibility = View.VISIBLE
                        tvStatus.text = "解析中..."
                    }

                    override fun onError(error: Int) {
                        isListening = false
                        resetMicScale()
                        updateActionButtonUi()
                        statusContainer.visibility = View.GONE
                        etCommand.hint = "聞き取れませんでした。もう一度お試しください"
                    }

                    override fun onResults(results: Bundle?) {
                        isListening = false
                        resetMicScale()
                        updateActionButtonUi()

                        val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                        if (!matches.isNullOrEmpty()) {
                            val recognizedText = matches[0]
                            etCommand.setText(recognizedText)
                            submitCommand(recognizedText)
                        }
                    }

                    override fun onPartialResults(partialResults: Bundle?) {
                        val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                        if (!matches.isNullOrEmpty()) {
                            val partial = matches[0]
                            etCommand.setText(partial)
                            etCommand.setSelection(partial.length)
                        }
                    }

                    override fun onEvent(eventType: Int, params: Bundle?) {}
                })
            }

            val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                putExtra(RecognizerIntent.EXTRA_LANGUAGE, "ja-JP")
                putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
                putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
            }

            speechRecognizer?.startListening(intent)
        } catch (e: Exception) {
            etCommand.hint = "話しかけるか、入力..."
        }
    }

    private fun stopListening() {
        if (isListening) {
            try {
                speechRecognizer?.stopListening()
            } catch (ignored: Exception) {}
            isListening = false
            resetMicScale()
            updateActionButtonUi()
        }
    }

    private fun resetMicScale() {
        btnAction.animate().scaleX(1.0f).scaleY(1.0f).setDuration(120).start()
    }

    private fun updateActionButtonUi() {
        val hasText = etCommand.text.toString().trim().isNotEmpty()
        if (hasText) {
            iconAction.setImageResource(R.drawable.ic_send)
            btnAction.setBackgroundResource(R.drawable.bg_mic_button)
        } else {
            iconAction.setImageResource(R.drawable.ic_mic)
            if (isListening) {
                btnAction.setBackgroundResource(R.drawable.bg_mic_button_listening)
            } else {
                btnAction.setBackgroundResource(R.drawable.bg_mic_button)
            }
        }
    }

    private fun submitCommand(prompt: String) {
        stopListening()
        statusContainer.visibility = View.VISIBLE
        loadingSpinner.visibility = View.VISIBLE
        tvStatus.text = "実行中..."
        tvStatus.setTextColor(Color.parseColor("#e2e8f0"))
        btnAction.isEnabled = false

        Thread {
            val (success, message) = NetworkUtils.executeAssistantCommand(this, prompt)
            mainHandler.post {
                loadingSpinner.visibility = View.GONE
                btnAction.isEnabled = true
                tvStatus.text = message

                if (success) {
                    tvStatus.setTextColor(Color.parseColor("#60a5fa"))
                    vibrateDevice()
                    autoDismissRunnable = Runnable {
                        dismissWithAnimation()
                    }
                    mainHandler.postDelayed(autoDismissRunnable!!, 2000)
                } else {
                    tvStatus.setTextColor(Color.parseColor("#f87171"))
                }
            }
        }.start()
    }

    private fun cancelAutoDismiss() {
        autoDismissRunnable?.let {
            mainHandler.removeCallbacks(it)
            autoDismissRunnable = null
        }
    }

    private fun openDashboard() {
        cancelAutoDismiss()
        stopListening()

        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        startActivity(intent)
        finish()
        overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out)
    }

    private fun dismissWithAnimation() {
        cancelAutoDismiss()
        stopListening()
        finish()
        overridePendingTransition(0, R.anim.slide_out_bottom)
    }

    override fun onBackPressed() {
        dismissWithAnimation()
    }

    private fun hideKeyboard() {
        val imm = getSystemService(Context.INPUT_METHOD_SERVICE) as? InputMethodManager
        imm?.hideSoftInputFromWindow(etCommand.windowToken, 0)
    }

    private fun vibrateDevice() {
        try {
            val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val vibratorManager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
                vibratorManager?.defaultVibrator
            } else {
                @Suppress("DEPRECATION")
                getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator?.vibrate(VibrationEffect.createOneShot(45, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                @Suppress("DEPRECATION")
                vibrator?.vibrate(45)
            }
        } catch (ignored: Exception) {}
    }

    override fun onDestroy() {
        cancelAutoDismiss()
        try {
            speechRecognizer?.destroy()
        } catch (ignored: Exception) {}
        speechRecognizer = null
        super.onDestroy()
    }
}
