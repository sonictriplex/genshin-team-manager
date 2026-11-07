package de.sonictriplex.genshinteams.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import de.sonictriplex.genshinteams.BuildConfig

@Composable
fun LoginScreen(vm: AppViewModel) {
    // Nur in Debug und Staging bearbeitbar; im Release ist der Server fest (BuildConfig.DEFAULT_SERVER_URL)
    var server by rememberSaveable { mutableStateOf(vm.serverUrl) }
    var username by rememberSaveable { mutableStateOf(vm.session.username) }
    var password by rememberSaveable { mutableStateOf("") }

    Column(
        Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp, Alignment.CenterVertically),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("Genshin Teams", style = MaterialTheme.typography.headlineMedium)
        if (!BuildConfig.SERVER_EDITABLE) {
            // Zeigt, wohin die Anmeldung geht (nur der Host, ohne https://)
            Text(
                BuildConfig.DEFAULT_SERVER_URL.removePrefix("https://").removePrefix("http://"),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Column(Modifier.widthIn(max = 420.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            if (BuildConfig.SERVER_EDITABLE) {
                OutlinedTextField(
                    server, { server = it }, label = { Text("Server") }, singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri),
                    modifier = Modifier.fillMaxWidth(),
                )
            }
            OutlinedTextField(
                username, { username = it }, label = { Text("Benutzername") }, singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
            OutlinedTextField(
                password, { password = it }, label = { Text("Passwort") }, singleLine = true,
                visualTransformation = PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                modifier = Modifier.fillMaxWidth(),
            )
            vm.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            Button(
                onClick = { vm.login(server, username, password) },
                enabled = !vm.busy,
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (vm.busy) CircularProgressIndicator(Modifier.padding(2.dp), strokeWidth = 2.dp) else Text("Anmelden")
            }
        }
    }
}
