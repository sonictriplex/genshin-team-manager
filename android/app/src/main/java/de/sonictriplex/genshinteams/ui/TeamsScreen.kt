package de.sonictriplex.genshinteams.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TeamsScreen(vm: AppViewModel, onOpenCharacter: (String) -> Unit, onNewTeam: () -> Unit, onEditTeam: (String) -> Unit) {
    val data = vm.userData
    var deleting by remember { mutableStateOf<String?>(null) }
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Teams") },
                actions = {
                    TextButton(onClick = onNewTeam) { Text("Neues Team") }
                    TextButton(onClick = vm::refresh, enabled = !vm.busy) { Text("Neu laden") }
                    TextButton(onClick = vm::logout, enabled = !vm.busy) { Text("Abmelden") }
                },
            )
        },
    ) { padding ->
        Column(Modifier.fillMaxSize().padding(padding)) {
            vm.error?.let { Text(it, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(16.dp)) }
            when {
                data == null && vm.busy -> CircularProgressIndicator(Modifier.padding(24.dp).align(Alignment.CenterHorizontally))
                data == null -> Unit
                data.teams.isEmpty() -> Text("Noch keine Teams. Lege sie in der Web- oder Desktop-Version an.", Modifier.padding(16.dp))
                else -> LazyColumn(
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    items(data.teams, key = { it.name }) { team ->
                        Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(MaterialTheme.colorScheme.surface)) {
                            Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Text(team.name, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                                    TextButton(onClick = { onEditTeam(team.name) }) { Text("Bearbeiten") }
                                    TextButton(onClick = { deleting = team.name }) { Text("Löschen") }
                                }
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    team.members.forEach { member ->
                                        NameIcon(
                                            member, vm.stammdaten, 64.dp,
                                            Modifier.clickable { onOpenCharacter(member) },
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    deleting?.let { name ->
        AlertDialog(
            onDismissRequest = { deleting = null },
            title = { Text("Team löschen?") },
            text = { Text("Das Team „$name“ wird gelöscht. Die Builds der Charaktere bleiben erhalten.") },
            confirmButton = { TextButton(onClick = { vm.deleteTeam(name); deleting = null }) { Text("Löschen") } },
            dismissButton = { TextButton(onClick = { deleting = null }) { Text("Abbrechen") } },
        )
    }
}
