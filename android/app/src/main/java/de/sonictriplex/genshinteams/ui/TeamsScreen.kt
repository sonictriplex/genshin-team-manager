package de.sonictriplex.genshinteams.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Box
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun TeamsScreen(vm: AppViewModel, onOpenCharacter: (String) -> Unit, onNewTeam: () -> Unit, onEditTeam: (String) -> Unit) {
    val data = vm.userData
    var deleting by remember { mutableStateOf<String?>(null) }
    var menuOpen by remember { mutableStateOf(false) }
    Scaffold(
        topBar = {
            AppTopBar(
                title = "Team & Build Manager",
                actions = {
                    IconButton(onClick = vm::refresh, enabled = !vm.busy) {
                        Icon(Icons.Filled.Refresh, contentDescription = "Neu laden")
                    }
                    Box {
                        IconButton(onClick = { menuOpen = true }) {
                            Icon(Icons.Filled.MoreVert, contentDescription = "Menü")
                        }
                        DropdownMenu(menuOpen, { menuOpen = false }) {
                            DropdownMenuItem(
                                text = { Text("Abmelden") },
                                onClick = { menuOpen = false; vm.logout() },
                                enabled = !vm.busy,
                            )
                        }
                    }
                },
            )
        },
        // Neue Teams lassen sich nur mit Verbindung anlegen
        floatingActionButton = {
            if (!vm.offline) {
                FloatingActionButton(onClick = onNewTeam) {
                    Icon(Icons.Filled.Add, contentDescription = "Neues Team")
                }
            }
        },
    ) { padding ->
        Column(Modifier.fillMaxSize().padding(padding)) {
            if (vm.busy && data != null) LinearProgressIndicator(Modifier.fillMaxWidth())
            if (vm.offline) OfflineBanner(vm.dataSavedAt)
            vm.error?.let { Text(it, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(16.dp)) }
            when {
                data == null && vm.busy -> CircularProgressIndicator(Modifier.padding(24.dp).align(Alignment.CenterHorizontally))
                data == null -> Unit
                data.teams.isEmpty() -> Text("Noch keine Teams. Tippe auf „Neues Team“, um das erste anzulegen.", Modifier.padding(16.dp))
                else -> LazyColumn(
                    contentPadding = PaddingValues(start = 16.dp, top = 16.dp, end = 16.dp, bottom = 96.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    itemsIndexed(data.teams, key = { _, team -> team.name }) { index, team ->
                        AppCard(alpha = 0.4f) {
                            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                // Der Name bekommt den ganzen Platz; die Aktionen sind kompakte Symbole
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Text(
                                        team.name,
                                        style = MaterialTheme.typography.titleMedium,
                                        color = MaterialTheme.colorScheme.tertiary,
                                        maxLines = 2,
                                        overflow = TextOverflow.Ellipsis,
                                        modifier = Modifier.weight(1f),
                                    )
                                    IconButton(onClick = { vm.moveTeam(team.name, -1) }, enabled = !vm.offline && !vm.saving && index > 0) {
                                        Icon(Icons.Filled.KeyboardArrowUp, contentDescription = "Team nach oben")
                                    }
                                    IconButton(onClick = { vm.moveTeam(team.name, 1) }, enabled = !vm.offline && !vm.saving && index < data.teams.lastIndex) {
                                        Icon(Icons.Filled.KeyboardArrowDown, contentDescription = "Team nach unten")
                                    }
                                    IconButton(onClick = { onEditTeam(team.name) }, enabled = !vm.offline) {
                                        Icon(Icons.Filled.Edit, contentDescription = "Team bearbeiten")
                                    }
                                    IconButton(onClick = { deleting = team.name }, enabled = !vm.offline) {
                                        Icon(Icons.Filled.Delete, contentDescription = "Team löschen")
                                    }
                                }
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    team.members.forEach { member ->
                                        Column(Modifier.width(64.dp).clickable { onOpenCharacter(member) }, horizontalAlignment = Alignment.CenterHorizontally) {
                                            NameIcon(member, vm.stammdaten, 64.dp, level = data.builds.firstOrNull { it.name == member }?.level ?: 90, flatBackground = true)
                                            Text(member, style = MaterialTheme.typography.labelSmall, maxLines = 1, overflow = TextOverflow.Ellipsis)
                                        }
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
