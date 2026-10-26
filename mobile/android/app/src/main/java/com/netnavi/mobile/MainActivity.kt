package com.netnavi.mobile

import android.app.Activity
import android.content.Intent
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.drawable.GradientDrawable
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.StatFs
import android.provider.OpenableColumns
import android.view.Gravity
import android.view.View
import android.view.WindowInsets
import android.widget.Button
import android.widget.EditText
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.io.IOException
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean
import kotlin.math.min

private const val PICK_GGUF = 3108
private const val CONTEXT_TOKENS = 2048
private const val MAX_REPLY_TOKENS = 256
private val BG = Color.rgb(9, 16, 29)
private val PANEL = Color.rgb(18, 31, 48)
private val CYAN = Color.rgb(87, 226, 227)
private val WHITE = Color.rgb(235, 246, 251)
private val MUTED = Color.rgb(164, 182, 200)

class MainActivity : Activity() {
    private val worker = Executors.newSingleThreadExecutor()
    private val stopCopy = AtomicBoolean(false)
    private val conversation = mutableListOf<Pair<String, String>>()
    private lateinit var statusText: TextView
    private lateinit var importButton: Button
    private lateinit var loadButton: Button
    private lateinit var newChatButton: Button
    private lateinit var sendButton: Button
    private lateinit var stopButton: Button
    private lateinit var inputText: EditText
    private lateinit var transcript: LinearLayout
    private lateinit var scroller: ScrollView
    private var busy = false
    private var loaded = false

    private val modelFile: File get() = File(filesDir, "models/active-model.gguf")
    private val prefs by lazy { getSharedPreferences("netnavi-local", MODE_PRIVATE) }
    private fun dp(v: Int) = (resources.displayMetrics.density * v + 0.5f).toInt()
    private fun shape(fill: Int, border: Int? = null): GradientDrawable =
        GradientDrawable().apply {
            setColor(fill)
            cornerRadius = dp(10).toFloat()
            if (border != null) setStroke(dp(1), border)
        }
    private fun text(value: String, size: Float, color: Int): TextView =
        TextView(this).apply { this.text = value; textSize = size; setTextColor(color) }
    private fun action(label: String, onClick: () -> Unit): Button =
        Button(this).apply {
            text = label; textSize = 11f; isAllCaps = false
            setTextColor(Color.BLACK); background = shape(CYAN)
            setOnClickListener { onClick() }
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = BG
        window.navigationBarColor = BG
        buildScreen()
        restoreHistory()
        showStatus(if (modelFile.exists()) "MODEL FOUND · Tap LOAD MODEL" else "NO MODEL · Import a GGUF")
        setBusy(false)
    }

    private fun buildScreen() {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(BG)
            setPadding(dp(12), dp(10), dp(12), dp(10))
        }
        if (Build.VERSION.SDK_INT >= 30) {
            root.setOnApplyWindowInsetsListener { view, insets ->
                val bars = insets.getInsets(WindowInsets.Type.systemBars())
                view.setPadding(dp(12) + bars.left, dp(10) + bars.top,
                    dp(12) + bars.right, dp(10) + bars.bottom)
                insets
            }
        } else root.fitsSystemWindows = true

        val header = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL
        }
        header.addView(NaviAvatar(this), LinearLayout.LayoutParams(dp(64), dp(64)))
        val brand = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL; setPadding(dp(12), 0, 0, 0)
        }
        brand.addView(text("NET.NAVI  //  PET", 21f, WHITE))
        brand.addView(text("PERSONAL NAVIGATOR · LOCAL", 10f, CYAN))
        header.addView(brand)
        root.addView(header)

        statusText = text("OFFLINE", 11f, MUTED).apply {
            background = shape(PANEL, Color.rgb(42, 71, 85))
            setPadding(dp(12), dp(10), dp(12), dp(10))
        }
        root.addView(statusText, LinearLayout.LayoutParams(-1, -2).apply {
            topMargin = dp(10); bottomMargin = dp(10)
        })

        val controls = LinearLayout(this)
        importButton = action("IMPORT GGUF") { pickModel() }
        loadButton = action("LOAD MODEL") { loadCurrentModel() }
        newChatButton = action("NEW CHAT") { clearChat() }
        controls.addView(importButton, LinearLayout.LayoutParams(0, dp(48), 1f).apply { rightMargin = dp(4) })
        controls.addView(loadButton, LinearLayout.LayoutParams(0, dp(48), 1f).apply { rightMargin = dp(4) })
        controls.addView(newChatButton, LinearLayout.LayoutParams(0, dp(48), 1f))
        root.addView(controls)

        scroller = ScrollView(this).apply {
            fillViewport = true
            background = shape(PANEL, Color.rgb(34, 66, 78))
        }
        transcript = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(10), dp(12), dp(10), dp(12))
        }
        scroller.addView(transcript, FrameLayout.LayoutParams(-1, -2))
        root.addView(scroller, LinearLayout.LayoutParams(-1, 0, 1f).apply {
            topMargin = dp(12); bottomMargin = dp(10)
        })

        val composer = LinearLayout(this).apply { gravity = Gravity.CENTER_VERTICAL }
        inputText = EditText(this).apply {
            hint = "Message your Navi..."
            setHintTextColor(MUTED); setTextColor(WHITE)
            textSize = 14f; maxLines = 3
            background = shape(PANEL, Color.rgb(56, 95, 105))
            setPadding(dp(10), dp(8), dp(10), dp(8))
        }
        composer.addView(inputText, LinearLayout.LayoutParams(0, dp(52), 1f))
        sendButton = action("SEND") { sendMessage() }
        composer.addView(sendButton, LinearLayout.LayoutParams(dp(64), dp(52)).apply { leftMargin = dp(5) })
        stopButton = action("JACK OUT") {
            stopCopy.set(true)
            NativeEngine.requestStop()
            showStatus("STOP REQUESTED")
        }.apply {
            setTextColor(WHITE)
            background = shape(Color.rgb(131, 45, 65))
        }
        composer.addView(stopButton, LinearLayout.LayoutParams(dp(80), dp(52)).apply { leftMargin = dp(5) })
        root.addView(composer)
        setContentView(root)
    }

    private fun showStatus(value: String) { statusText.text = "● OFFLINE  |  " + value }
    private fun setBusy(value: Boolean) {
        busy = value
        importButton.isEnabled = !value
        loadButton.isEnabled = !value && modelFile.exists()
        newChatButton.isEnabled = !value
        sendButton.isEnabled = !value && loaded
        stopButton.isEnabled = value
    }
    private fun scrollBottom() = scroller.post { scroller.fullScroll(View.FOCUS_DOWN) }
    private fun addBubble(role: String, content: String): TextView {
        val isUser = role == "user"
        val message = text(content, 14f, WHITE).apply {
            setPadding(dp(12), dp(10), dp(12), dp(10))
            background = shape(if (isUser) Color.rgb(31, 70, 83) else Color.rgb(27, 40, 65),
                if (isUser) CYAN else Color.rgb(67, 82, 112))
        }
        val block = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(0, dp(5), 0, dp(9))
            addView(text(if (isUser) "OPERATOR" else "NET.NAVI", 10f, CYAN))
            addView(message, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(4) })
        }
        transcript.addView(block)
        scrollBottom()
        return message
    }
    private fun restoreHistory() {
        try {
            val a = JSONArray(prefs.getString("chat", "[]"))
            for (i in 0 until a.length()) {
                val o = a.getJSONObject(i)
                val role = o.getString("role"); val content = o.getString("content")
                if (role == "user" || role == "assistant") {
                    conversation.add(role to content)
                    addBubble(role, content)
                }
            }
        } catch (_: Exception) {
            conversation.clear(); transcript.removeAllViews()
        }
        if (conversation.isEmpty()) addBubble("assistant", "Jack in to begin. Import your local GGUF model.")
    }
    private fun persistHistory() {
        val a = JSONArray()
        conversation.takeLast(40).forEach { (role, content) ->
            a.put(JSONObject().put("role", role).put("content", content))
        }
        prefs.edit().putString("chat", a.toString()).apply()
    }
    private fun clearChat() {
        conversation.clear()
        prefs.edit().remove("chat").apply()
        transcript.removeAllViews()
        addBubble("assistant", "New operator session. Conversation cleared.")
    }
    private fun pickModel() {
        startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE); type = "*/*"
        }, PICK_GGUF)
    }
    @Suppress("DEPRECATION")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == PICK_GGUF && resultCode == RESULT_OK) {
            data?.data?.let { importModel(it) }
        }
    }

    private fun importModel(uri: Uri) {
        if (busy) return
        stopCopy.set(false); setBusy(true); showStatus("IMPORTING MODEL...")
        worker.execute {
            val incoming = File(filesDir, "models/incoming.gguf")
            try {
                incoming.parentFile?.mkdirs()
                val bytesNeeded = contentResolver.query(uri, arrayOf(OpenableColumns.SIZE), null, null, null)
                    ?.use { c -> if (c.moveToFirst() && !c.isNull(0)) c.getLong(0) else -1L } ?: -1L
                if (bytesNeeded >= 0 &&
                    StatFs(filesDir.absolutePath).availableBytes < bytesNeeded + 32L * 1024L * 1024L) {
                    throw IOException("Not enough free storage")
                }
                var written = 0L
                contentResolver.openInputStream(uri).use { source ->
                    if (source == null) throw IOException("Cannot read selected file")
                    FileOutputStream(incoming).use { dest ->
                        val buffer = ByteArray(256 * 1024)
                        while (true) {
                            if (stopCopy.get()) throw IOException("Import cancelled")
                            val n = source.read(buffer)
                            if (n < 0) break
                            dest.write(buffer, 0, n)
                            written += n
                            if (written % (16L * 1024L * 1024L) < n) {
                                val mb = written / (1024L * 1024L)
                                runOnUiThread { showStatus("IMPORTING · $mb MiB copied") }
                            }
                        }
                    }
                }
                val signature = ByteArray(4)
                FileInputStream(incoming).use {
                    if (it.read(signature) != 4 || String(signature, Charsets.US_ASCII) != "GGUF") {
                        throw IOException("Not a GGUF. Export merged model to GGUF first.")
                    }
                }
                NativeEngine.unload()
                loaded = false
                if (modelFile.exists() && !modelFile.delete()) throw IOException("Cannot replace old model")
                if (!incoming.renameTo(modelFile)) throw IOException("Cannot move imported GGUF")
                runOnUiThread { showStatus("IMPORTED · loading model") }
                loadModelOnWorker()
            } catch (e: Exception) {
                incoming.delete()
                runOnUiThread {
                    showStatus("IMPORT FAILED · " + (e.message ?: "unknown error"))
                    setBusy(false)
                }
            }
        }
    }
    private fun loadCurrentModel() {
        if (busy || !modelFile.exists()) return
        setBusy(true); showStatus("LOADING MODEL · CPU")
        worker.execute { loadModelOnWorker() }
    }
    private fun loadModelOnWorker() {
        try {
            val threads = min(4, Runtime.getRuntime().availableProcessors().coerceAtLeast(1))
            val result = NativeEngine.loadModel(modelFile.absolutePath, CONTEXT_TOKENS, threads)
            runOnUiThread {
                loaded = !result.startsWith("ERROR:")
                showStatus(if (loaded) "READY · " + result else result)
                setBusy(false)
            }
        } catch (e: Throwable) {
            runOnUiThread {
                loaded = false
                showStatus("LOAD FAILED · " + (e.message ?: "unknown error"))
                setBusy(false)
            }
        }
    }
    private fun sendMessage() {
        if (busy || !loaded) return
        val question = inputText.text.toString().trim()
        if (question.isEmpty()) return
        inputText.text.clear()
        conversation.add("user" to question)
        persistHistory()
        addBubble("user", question)
        val reply = addBubble("assistant", "…")
        val messages = listOf("system" to
            "You are NET.Navi, a concise and accurate local AI companion. You have no internet access or external tools. /no_think") +
            conversation.takeLast(8)
        setBusy(true); showStatus("GENERATING · local CPU")
        worker.execute {
            var answer = ""
            try {
                val result = NativeEngine.generate(
                    messages.map { it.first }.toTypedArray(),
                    messages.map { it.second }.toTypedArray(),
                    MAX_REPLY_TOKENS,
                    object : NativeEngine.StreamCallback {
                        override fun onText(utf8: ByteArray) {
                            answer = String(utf8, Charsets.UTF_8)
                            val snapshot = answer
                            runOnUiThread { reply.text = snapshot }
                        }
                    })
                val completed = answer.trim().ifEmpty {
                    if (result.startsWith("ERROR:")) result else "(No response generated)"
                }
                runOnUiThread {
                    reply.text = completed
                    conversation.add("assistant" to completed)
                    persistHistory()
                    showStatus(result)
                    setBusy(false)
                    scrollBottom()
                }
            } catch (e: Throwable) {
                runOnUiThread {
                    reply.text = "Generation failed: " + e.message
                    showStatus("GENERATION FAILED"); setBusy(false)
                }
            }
        }
    }
    override fun onDestroy() {
        stopCopy.set(true)
        NativeEngine.requestStop()
        worker.execute { NativeEngine.unload() }
        worker.shutdown()
        super.onDestroy()
    }
}

object NativeEngine {
    init { System.loadLibrary("navi_native") }
    interface StreamCallback { fun onText(utf8: ByteArray) }
    external fun loadModel(path: String, contextTokens: Int, threads: Int): String
    external fun generate(roles: Array<String>, messages: Array<String>, maxTokens: Int, callback: StreamCallback): String
    external fun requestStop()
    external fun unload()
}

private class NaviAvatar(context: android.content.Context) : View(context) {
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
    override fun onDraw(canvas: Canvas) {
        val size = min(width, height) / 64f
        canvas.save(); canvas.scale(size, size)
        paint.style = Paint.Style.STROKE; paint.strokeWidth = 2f
        paint.color = CYAN; canvas.drawCircle(32f, 32f, 29f, paint)
        paint.color = Color.rgb(30, 96, 108); canvas.drawCircle(32f, 32f, 25f, paint)
        paint.style = Paint.Style.FILL
        paint.color = Color.rgb(35, 133, 147)
        canvas.drawRoundRect(14f, 18f, 50f, 49f, 12f, 12f, paint)
        paint.color = CYAN; canvas.drawRoundRect(18f, 22f, 46f, 45f, 8f, 8f, paint)
        paint.color = BG
        canvas.drawRoundRect(23f, 30f, 29f, 34f, 2f, 2f, paint)
        canvas.drawRoundRect(35f, 30f, 41f, 34f, 2f, 2f, paint)
        canvas.drawRoundRect(28f, 39f, 36f, 41f, 1f, 1f, paint)
        canvas.restore()
    }
}
