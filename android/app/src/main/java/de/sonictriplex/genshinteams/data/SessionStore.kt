package de.sonictriplex.genshinteams.data

import android.content.Context
import androidx.core.content.edit

/** Speichert Server-Adresse, Benutzername und API-Token im app-privaten Speicher. */
class SessionStore(context: Context) {
    private val prefs = context.getSharedPreferences("session", Context.MODE_PRIVATE)

    var serverUrl: String
        get() = prefs.getString("server_url", "") ?: ""
        set(value) = prefs.edit { putString("server_url", value) }

    var username: String
        get() = prefs.getString("username", "") ?: ""
        set(value) = prefs.edit { putString("username", value) }

    var token: String?
        get() = prefs.getString("token", null)
        set(value) = prefs.edit { if (value == null) remove("token") else putString("token", value) }
}
