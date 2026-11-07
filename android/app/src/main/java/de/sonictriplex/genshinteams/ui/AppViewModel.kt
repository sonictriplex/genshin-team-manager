package de.sonictriplex.genshinteams.ui

import android.app.Application
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import de.sonictriplex.genshinteams.BuildConfig
import de.sonictriplex.genshinteams.data.ApiClient
import de.sonictriplex.genshinteams.data.ApiException
import de.sonictriplex.genshinteams.data.Build
import de.sonictriplex.genshinteams.data.ExchangeFile
import de.sonictriplex.genshinteams.data.SessionStore
import de.sonictriplex.genshinteams.data.NetworkException
import de.sonictriplex.genshinteams.data.StammdatenRepository
import de.sonictriplex.genshinteams.data.Team
import de.sonictriplex.genshinteams.data.UnauthorizedException
import de.sonictriplex.genshinteams.data.UserDataCache
import de.sonictriplex.genshinteams.data.validateRegistration
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Zustand der App: Anmeldung, geladene Nutzerdaten, Lade- und Fehlerstatus.
 *
 * Offline-Cache: Beim Start erscheinen sofort die zuletzt geladenen Teams und Builds, danach wird im
 * Hintergrund aktualisiert. Ist der Server nicht erreichbar, bleibt der Cache sichtbar ([offline]) und
 * Änderungen sind gesperrt, bis wieder eine Verbindung besteht.
 */
class AppViewModel(app: Application) : AndroidViewModel(app) {
    val session = SessionStore(app)
    val stammdaten = StammdatenRepository(app)
    private val cache = UserDataCache(app.filesDir)

    var loggedIn by mutableStateOf(session.token != null)
        private set
    var busy by mutableStateOf(false)
        private set
    var error by mutableStateOf<String?>(null)
        private set
    var saving by mutableStateOf(false)
        private set
    var userData by mutableStateOf<ExchangeFile?>(null)
        private set

    /** true, wenn die angezeigten Daten aus dem Cache stammen, weil der Server nicht erreichbar war. */
    var offline by mutableStateOf(false)
        private set

    /** Zeitpunkt (ms), zu dem [userData] zuletzt mit dem Server übereinstimmte. */
    var dataSavedAt by mutableStateOf<Long?>(null)
        private set

    init {
        if (loggedIn) {
            cache.load(serverUrl, session.username)?.let {
                userData = it.data
                dataSavedAt = it.savedAt
            }
            refresh()
        }
    }

    /**
     * Der Server: im Release immer die fest eingestellte Adresse (eine früher gespeicherte wird ignoriert),
     * in Debug und Staging die zuletzt eingegebene.
     */
    val serverUrl: String
        get() = if (BuildConfig.SERVER_EDITABLE) session.serverUrl.ifEmpty { BuildConfig.DEFAULT_SERVER_URL } else BuildConfig.DEFAULT_SERVER_URL

    private fun api(baseUrl: String = serverUrl) = ApiClient(baseUrl, { session.token })

    fun login(serverUrl: String, username: String, password: String) {
        val url = serverUrl.trim().trimEnd('/')
        if (url.isEmpty() || username.isBlank() || password.isEmpty()) {
            error = "Bitte Server, Benutzername und Passwort eingeben."
            return
        }
        authenticate(url) { it.login(username.trim(), password) }
    }

    /** Legt ein neues Konto an und meldet danach an (Ablauf wie [login]). */
    fun register(serverUrl: String, username: String, password: String, repeat: String) {
        val url = serverUrl.trim().trimEnd('/')
        if (url.isEmpty()) {
            error = "Bitte einen Server angeben."
            return
        }
        validateRegistration(username, password, repeat)?.let { error = it; return }
        authenticate(url) { it.register(username.trim(), password) }
    }

    /** Gemeinsamer Ablauf von Anmeldung und Registrierung: Token holen, Sitzung speichern, Daten laden. */
    private fun authenticate(url: String, action: suspend (ApiClient) -> Pair<String, String>) {
        viewModelScope.launch {
            busy = true
            error = null
            try {
                val (token, name) = action(api(url))
                session.serverUrl = url
                session.username = name
                session.token = token
                loggedIn = true
                refresh()
            } catch (e: ApiException) {
                error = e.message
            } finally {
                busy = false
            }
        }
    }

    fun refresh() {
        viewModelScope.launch {
            busy = true
            error = null
            try {
                val fresh = api().fetchUserData()
                userData = fresh
                offline = false
                storeCache(fresh)
            } catch (e: UnauthorizedException) {
                clearSession()
                error = "Sitzung abgelaufen. Bitte erneut anmelden."
            } catch (e: NetworkException) {
                // Mit Cache: den letzten Stand weiter zeigen. Ohne Cache bleibt nur die Fehlermeldung.
                if (userData != null) offline = true else error = e.message
            } catch (e: ApiException) {
                error = e.message
            } finally {
                busy = false
            }
        }
    }

    /** Ruft die Daten erneut ab, wenn der Server zuletzt nicht erreichbar war (z. B. beim Zurückkehren in die App). */
    fun retryIfOffline() {
        if (loggedIn && offline && !busy) refresh()
    }

    private suspend fun storeCache(data: ExchangeFile) {
        val now = System.currentTimeMillis()
        dataSavedAt = now
        val server = serverUrl
        val user = session.username
        withContext(Dispatchers.IO) { cache.save(server, user, data, now) }
    }

    fun logout() {
        viewModelScope.launch {
            busy = true
            error = null
            try { api().logout() } finally { clearSession(); busy = false }
        }
    }

    /** Führt eine Schreibaktion aus: Ladezustand, Fehlermeldung und abgelaufene Sitzung einheitlich behandelt. */
    private fun write(action: suspend (ApiClient) -> Unit, onSuccess: () -> Unit) {
        viewModelScope.launch {
            saving = true
            error = null
            try {
                action(api())
                onSuccess()
                userData?.let { storeCache(it) }   // der Cache folgt den eigenen Änderungen
            } catch (e: UnauthorizedException) {
                clearSession()
                error = "Sitzung abgelaufen. Bitte erneut anmelden."
            } catch (e: ApiException) {
                error = e.message
            } finally {
                saving = false
            }
        }
    }

    /** Speichert einen Build auf dem Server und übernimmt ihn danach in die lokale Ansicht. */
    fun saveBuild(build: Build, onSaved: () -> Unit) = write({ it.saveBuild(build) }) {
        userData = userData?.let { d -> d.copy(builds = d.builds.filterNot { it.name == build.name } + build) }
        onSaved()
    }

    /**
     * Speichert ein Team. [originalName] ist der bisherige Name beim Bearbeiten (null bei einem neuen Team);
     * wurde das Team umbenannt, wird der alte Eintrag danach gelöscht.
     */
    fun saveTeam(team: Team, originalName: String?, onSaved: () -> Unit) = write({ api ->
        api.saveTeam(team)
        if (originalName != null && originalName != team.name) api.deleteTeam(originalName)
    }) {
        userData = userData?.let { d ->
            val inPlace = originalName != null && originalName == team.name
            d.copy(
                teams = if (inPlace) {
                    d.teams.map { if (it.name == team.name) team else it }
                } else {
                    // Der Server sortiert nach Anlage: neue und umbenannte Teams stehen am Ende
                    d.teams.filterNot { it.name == team.name || it.name == originalName } + team
                },
            )
        }
        onSaved()
    }

    fun deleteTeam(name: String) = write({ it.deleteTeam(name) }) {
        userData = userData?.let { d -> d.copy(teams = d.teams.filterNot { it.name == name }) }
    }

    fun dismissError() { error = null }

    private fun clearSession() {
        session.token = null
        loggedIn = false
        userData = null
        offline = false
        dataSavedAt = null
        cache.clear()   // Daten eines abgemeldeten Nutzers nicht auf dem Gerät lassen
    }
}
