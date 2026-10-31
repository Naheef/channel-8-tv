package tv.channel8.app

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL

object PlaylistResolver {
    /**
     * Fetches the M3U playlist and returns the first stream URL in it (resolved against the
     * playlist URL if relative). Throws on network failure so the caller can retry.
     */
    suspend fun resolve(playlistUrl: String = Config.PLAYLIST_URL): String = withContext(Dispatchers.IO) {
        val conn = (URL(playlistUrl).openConnection() as HttpURLConnection).apply {
            connectTimeout = 5_000
            readTimeout = 5_000
        }
        try {
            if (conn.responseCode !in 200..299) error("Playlist HTTP ${conn.responseCode}")
            val body = conn.inputStream.bufferedReader().use { it.readText() }
            val entry = body.lineSequence()
                .map { it.trim().trimStart('﻿') }
                .firstOrNull { it.isNotEmpty() && !it.startsWith("#") }
            entry?.let { URL(URL(playlistUrl), it).toString() } ?: Config.FALLBACK_STREAM_URL
        } finally {
            conn.disconnect()
        }
    }
}
