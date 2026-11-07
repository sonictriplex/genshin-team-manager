package de.sonictriplex.genshinteams.data

import android.os.Build
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.Serializable
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException
import java.util.concurrent.TimeUnit

/** Fehler der Web-API mit verständlicher Meldung für die Oberfläche. */
open class ApiException(message: String, cause: Throwable? = null) : Exception(message, cause)

/** Der Token ist ungültig oder abgelaufen: neu anmelden. */
class UnauthorizedException(message: String) : ApiException(message)

@Serializable
private data class TokenRequest(val username: String, val password: String, val device: String)

@Serializable
private data class TokenResponse(val token: String, val username: String = "", val expires_at: String = "")

@Serializable
private data class ErrorResponse(val error: String = "")

/**
 * Zugriff auf die PHP-API der Web-Version (web/api/). Die App spricht nie direkt mit MySQL.
 * [baseUrl] ist die Adresse des Servers ohne /api, z. B. https://example.org
 */
class ApiClient(
    private val baseUrl: String,
    private val tokenProvider: () -> String?,
    private val http: OkHttpClient = defaultClient,
) {
    private fun url(endpoint: String) = baseUrl.trimEnd('/') + "/api/" + endpoint

    /** Meldet sich an und gibt Token und Benutzernamen zurück. */
    suspend fun login(username: String, password: String): Pair<String, String> {
        val body = AppJson.encodeToString(TokenRequest.serializer(), TokenRequest(username, password, deviceName()))
        val request = Request.Builder().url(url("auth.php?action=token"))
            .post(body.toRequestBody(JSON_TYPE)).build()
        val response = execute(request)
        val parsed = AppJson.decodeFromString(TokenResponse.serializer(), response)
        return parsed.token to parsed.username.ifBlank { username }
    }

    /** Widerruft den Token auf dem Server. Fehler sind unkritisch, die lokale Abmeldung zählt. */
    suspend fun logout() {
        val request = Request.Builder().url(url("auth.php?action=logout"))
            .header("Authorization", "Bearer ${tokenProvider() ?: return}")
            .post("".toRequestBody(JSON_TYPE)).build()
        try { execute(request) } catch (_: ApiException) { }
    }

    /** Builds und Teams des angemeldeten Nutzers im gemeinsamen Austauschformat. */
    suspend fun fetchUserData(): ExchangeFile {
        val token = tokenProvider() ?: throw UnauthorizedException("Nicht eingeloggt")
        val request = Request.Builder().url(url("transfer.php"))
            .header("Authorization", "Bearer $token").get().build()
        return try {
            parseExchange(execute(request))
        } catch (e: IllegalArgumentException) {
            throw ApiException(e.message ?: "Ungültige Antwort des Servers", e)
        } catch (e: kotlinx.serialization.SerializationException) {
            throw ApiException("Ungültige Antwort des Servers", e)
        }
    }

    private suspend fun execute(request: Request): String = withContext(Dispatchers.IO) {
        try {
            http.newCall(request).execute().use { response ->
                val text = response.body.string()
                if (response.isSuccessful) return@use text
                val message = runCatching { AppJson.decodeFromString(ErrorResponse.serializer(), text).error }
                    .getOrNull().orEmpty().ifBlank { "Serverfehler (${response.code})" }
                if (response.code == 401 && request.header("Authorization") != null) throw UnauthorizedException(message)
                throw ApiException(message)
            }
        } catch (e: IOException) {
            throw ApiException("Server nicht erreichbar. Adresse und Netzwerk prüfen.", e)
        } catch (e: IllegalArgumentException) {
            throw ApiException("Ungültige Server-Adresse.", e)
        }
    }

    private fun deviceName() = "${Build.MANUFACTURER} ${Build.MODEL}".trim().take(100)

    companion object {
        private val JSON_TYPE = "application/json; charset=utf-8".toMediaType()
        private val defaultClient = OkHttpClient.Builder()
            .callTimeout(30, TimeUnit.SECONDS)
            .build()
    }
}
