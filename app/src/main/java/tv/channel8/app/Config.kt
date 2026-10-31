package tv.channel8.app

object Config {
    /**
     * Base URL of the stream server. Change this one value to point the app elsewhere.
     * If you change the host, also update res/xml/network_security_config.xml (cleartext is scoped to it).
     */
    const val BASE_URL = "http://192.168.10.50:9798"

    const val PLAYLIST_URL = "$BASE_URL/playlist.m3u"

    /** Used if the playlist can't be parsed but the server is reachable. */
    const val FALLBACK_STREAM_URL = "$BASE_URL/stream/stream.m3u8"

    /** Delay before each reconnect attempt (ms), backing off up to the max. */
    const val RETRY_MIN_MS = 2_000L
    const val RETRY_MAX_MS = 15_000L
}
