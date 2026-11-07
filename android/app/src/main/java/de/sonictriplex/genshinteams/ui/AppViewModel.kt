package de.sonictriplex.genshinteams.ui

import android.app.Application
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import de.sonictriplex.genshinteams.data.ApiClient
import de.sonictriplex.genshinteams.data.ApiException
import de.sonictriplex.genshinteams.data.Build
import de.sonictriplex.genshinteams.data.ExchangeFile
import de.sonictriplex.genshinteams.data.SessionStore
import de.sonictriplex.genshinteams.data.StammdatenRepository
import de.sonictriplex.genshinteams.data.Team
import de.sonictriplex.genshinteams.data.UnauthorizedException
import kotlinx.coroutines.launch

/** Zustand der App: Anmeldung, geladene Nutzerdaten, Lade- und Fehlerstatus. */
class AppViewModel(app: Application) : AndroidViewModel(app) {
    val session = SessionStore(app)
    val stammdaten = StammdatenRepository(app)

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

    private fun api(baseUrl: String = session.serverUrl) = ApiClient(baseUrl, { session.token })

    fun login(serverUrl: String, username: String, password: String) {
        val url = serverUrl.trim().trimEnd('/')
        if (url.isEmpty() || username.isBlank() || password.isEmpty()) {
            error = "Bitte Server, Benutzername und Passwort eingeben."
            return
        }
        viewModelScope.launch {
            busy = true
            error = null
            try {
                val (token, name) = api(url).login(username.trim(), password)
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
                userData = api().fetchUserData()
            } catch (e: UnauthorizedException) {
                clearSession()
                error = "Sitzung abgelaufen. Bitte erneut anmelden."
            } catch (e: ApiException) {
                error = e.message
            } finally {
                busy = false
            }
        }
    }

    fun logout() {
        viewModelScope.launch {
            busy = true
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
    }
}
