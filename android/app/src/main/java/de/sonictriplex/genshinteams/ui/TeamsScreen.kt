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
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TeamsScreen(vm: AppViewModel, onOpenCharacter: (String) -> Unit) {
    val data = vm.userData
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Teams") },
                actions = {
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
                                Text(team.name, style = MaterialTheme.typography.titleMedium)
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
}
