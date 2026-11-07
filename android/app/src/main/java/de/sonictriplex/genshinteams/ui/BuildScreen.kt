package de.sonictriplex.genshinteams.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
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
import de.sonictriplex.genshinteams.data.ARTIFACT_SLOTS
import de.sonictriplex.genshinteams.data.Build

/** Schreibgeschützte Ansicht des Builds eines Charakters (Bearbeiten folgt in einer späteren Version). */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BuildScreen(vm: AppViewModel, name: String, onBack: () -> Unit) {
    val character = vm.stammdaten.character(name)
    val build: Build? = vm.userData?.builds?.firstOrNull { it.name == name }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(name) },
                navigationIcon = { TextButton(onClick = onBack) { Text("Zurück") } },
            )
        },
    ) { padding ->
        Column(
            Modifier.fillMaxSize().padding(padding).verticalScroll(rememberScrollState()).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Row(horizontalArrangement = Arrangement.spacedBy(16.dp), verticalAlignment = Alignment.CenterVertically) {
                NameIcon(name, vm.stammdaten, 96.dp)
                Column {
                    if (character != null) {
                        Text(character.element, color = elementColor(character.element), style = MaterialTheme.typography.titleMedium)
                        Text("${character.rarity} ★ · ${character.weaponType} · ${character.region}")
                    }
                }
            }
            if (build == null) {
                Text("Für diesen Charakter ist noch kein Build gespeichert.")
                return@Column
            }
            Section("Charakter") {
                Text("Level ${build.level} · Sternbild C${build.constellation}")
                Text("Talente: ${build.talents.attack} / ${build.talents.skill} / ${build.talents.burst}")
            }
            Section("Waffe") {
                if (build.weapon.isBlank()) Text("Keine Waffe") else {
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        NameIcon(build.weapon, vm.stammdaten, 56.dp)
                        Column {
                            Text(build.weapon)
                            Text("Level ${build.weaponLevel} · Veredelung ${build.refinement}")
                        }
                    }
                }
            }
            Section("Artefakte") {
                val sets = listOf(build.artifact, build.artifact2).filter { it.isNotBlank() && !it.startsWith("—") }
                Text(if (sets.isEmpty()) "Kein Set" else sets.joinToString(" + "))
            }
            ARTIFACT_SLOTS.forEach { slotName ->
                val slot = build.artifactStats[slotName] ?: return@forEach
                Section("$slotName · ${slot.rarity} · +${slot.level}") {
                    Text("${slot.mainStat}: ${slot.mainValue}", style = MaterialTheme.typography.titleSmall)
                    slot.substats.filter { it.stat.isNotBlank() }.forEach { Text("${it.stat}  ${it.value}") }
                }
            }
        }
    }
}

@Composable
private fun Section(title: String, content: @Composable () -> Unit) {
    Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(MaterialTheme.colorScheme.surface)) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(title, style = MaterialTheme.typography.titleSmall, color = MaterialTheme.colorScheme.primary)
            content()
        }
    }
}
