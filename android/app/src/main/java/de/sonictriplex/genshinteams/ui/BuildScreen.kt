package de.sonictriplex.genshinteams.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.draw.clip
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import de.sonictriplex.genshinteams.data.ARTIFACT_SLOTS
import de.sonictriplex.genshinteams.data.Build

/** Ansicht des Builds eines Charakters; Bearbeiten über die Leiste oben. */
@Composable
fun BuildScreen(vm: AppViewModel, name: String, onBack: () -> Unit, onEdit: () -> Unit) {
    val character = vm.stammdaten.character(name)
    val build: Build? = vm.userData?.builds?.firstOrNull { it.name == name }

    Scaffold(
        topBar = {
            AppTopBar(
                title = name,
                navigation = NavigationKind.Back,
                onNavigate = onBack,
                actions = { TextButton(onClick = onEdit, enabled = !vm.offline) { Text(if (build == null) "Anlegen" else "Bearbeiten") } },
            )
        },
    ) { padding ->
        Column(Modifier.fillMaxSize().padding(padding)) {
            if (vm.offline) OfflineBanner(vm.dataSavedAt)
            ScrollingContent(twoColumns = true) {
                if (build == null) {
                    BuildHeader(name, character, vm)
                    Text("Für diesen Charakter ist noch kein Build gespeichert.")
                } else {
                    TwoColumns(
                        left = {
                            BuildHeader(name, character, vm)
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
                        },
                        right = {
                            ARTIFACT_SLOTS.forEach { slotName ->
                                val slot = build.artifactStats[slotName] ?: return@forEach
                                Section("$slotName · ${slot.rarity} · +${slot.level}") {
                                    Text("${slot.mainStat}: ${slot.mainValue}", style = MaterialTheme.typography.titleSmall)
                                    slot.substats.filter { it.stat.isNotBlank() }.forEach { Text("${it.stat}  ${it.value}") }
                                }
                            }
                        },
                    )
                }
            }
        }
    }
}

@Composable
private fun BuildHeader(name: String, character: de.sonictriplex.genshinteams.data.Character?, vm: AppViewModel) {
    Row(
        Modifier.fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(elementGradient(elementColor(character?.element.orEmpty()), 0.35f))
            .padding(12.dp),
        horizontalArrangement = Arrangement.spacedBy(16.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        NameIcon(name, vm.stammdaten, 96.dp)
        Column {
            if (character != null) {
                Text(character.element, color = elementColor(character.element), style = MaterialTheme.typography.titleMedium)
                // Zwei Zeilen statt einer langen, damit auch bei schmalem Display kein Wort umbricht
                Text("${character.rarity} ★ · ${character.region}")
                Text(character.weaponType)
            }
        }
    }
}

@Composable
private fun Section(title: String, content: @Composable () -> Unit) {
    AppCard {
        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(title, style = MaterialTheme.typography.titleSmall, color = MaterialTheme.colorScheme.tertiary)
            content()
        }
    }
}
