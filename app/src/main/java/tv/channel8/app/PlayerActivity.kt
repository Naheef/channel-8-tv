package tv.channel8.app

import android.os.Bundle
import android.util.Log
import android.view.KeyEvent
import android.view.View
import android.view.WindowManager
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import androidx.lifecycle.lifecycleScope
import androidx.media3.common.MediaItem
import androidx.media3.common.MimeTypes
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class PlayerActivity : AppCompatActivity() {

    private lateinit var playerView: PlayerView
    private lateinit var overlay: View
    private var player: ExoPlayer? = null
    private var connectJob: Job? = null
    private var retryDelay = Config.RETRY_MIN_MS

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_player)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        WindowCompat.getInsetsController(window, window.decorView).apply {
            hide(WindowInsetsCompat.Type.systemBars())
            systemBarsBehavior = WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        }
        playerView = findViewById(R.id.player_view)
        overlay = findViewById(R.id.reconnect_overlay)
    }

    override fun onStart() {
        super.onStart()
        val p = ExoPlayer.Builder(this).build().also { player = it }
        playerView.player = p
        p.playWhenReady = true
        p.addListener(object : Player.Listener {
            override fun onPlaybackStateChanged(state: Int) {
                when (state) {
                    Player.STATE_READY -> {
                        overlay.visibility = View.GONE
                        retryDelay = Config.RETRY_MIN_MS
                    }
                    // A live stream "ending" means the server stopped producing segments.
                    Player.STATE_ENDED -> scheduleReconnect("stream ended")
                    else -> Unit
                }
            }

            override fun onPlayerError(error: PlaybackException) {
                if (error.errorCode == PlaybackException.ERROR_CODE_BEHIND_LIVE_WINDOW) {
                    // Fell behind the live edge: jump back to live without showing the overlay.
                    p.seekToDefaultPosition()
                    p.prepare()
                    return
                }
                scheduleReconnect("player error: ${error.errorCodeName}")
            }
        })
        connect(initialDelay = 0)
    }

    override fun onStop() {
        super.onStop()
        connectJob?.cancel()
        playerView.player = null
        player?.release()
        player = null
    }

    private fun scheduleReconnect(reason: String) {
        Log.w(TAG, "Reconnecting: $reason")
        val d = retryDelay
        retryDelay = (retryDelay * 2).coerceAtMost(Config.RETRY_MAX_MS)
        connect(initialDelay = d)
    }

    private fun connect(initialDelay: Long) {
        overlay.visibility = View.VISIBLE
        connectJob?.cancel()
        connectJob = lifecycleScope.launch {
            if (initialDelay > 0) delay(initialDelay)
            val url = try {
                PlaylistResolver.resolve()
            } catch (e: Exception) {
                Log.w(TAG, "Playlist fetch failed", e)
                scheduleReconnect("server unreachable")
                return@launch
            }
            Log.i(TAG, "Playing $url")
            player?.apply {
                stop()
                setMediaItem(
                    MediaItem.Builder()
                        .setUri(url)
                        .apply { if (url.contains(".m3u8", ignoreCase = true)) setMimeType(MimeTypes.APPLICATION_M3U8) }
                        .setLiveConfiguration(MediaItem.LiveConfiguration.Builder().build())
                        .build()
                )
                prepare()
                play()
            }
        }
    }

    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        if (keyCode == KeyEvent.KEYCODE_BACK) {
            finish()
            return true
        }
        return super.onKeyDown(keyCode, event)
    }

    companion object {
        private const val TAG = "Channel8"
    }
}
