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
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import de.sonictriplex.genshinteams.data.ARTIFACT_SLOTS
import de.sonictriplex.genshinteams.data.Build
import de.sonictriplex.genshinteams.data.BuildOptions
import de.sonictriplex.genshinteams.data.Talents
import de.sonictriplex.genshinteams.data.normalized
import de.sonictriplex.genshinteams.data.withSlot
import de.sonictriplex.genshinteams.data.withSubstat

/** Bearbeiten und Speichern des Builds eines Charakters. Zurück verwirft ungespeicherte Änderungen. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EditBuildScreen(vm: AppViewModel, name: String, onDone: () -> Unit) {
    val character = vm.stammdaten.character(name)
    var build by remember {
        mutableStateOf((vm.userData?.builds?.firstOrNull { it.name == name } ?: Build(name = name)).normalized())
    }
    LaunchedEffect(Unit) { vm.dismissError() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("$name bearbeiten") },
                navigationIcon = { TextButton(onClick = onDone, enabled = !vm.saving) { Text("Abbrechen") } },
                actions = {
                    TextButton(onClick = { vm.saveBuild(build, onSaved = onDone) }, enabled = !vm.saving) {
                        if (vm.saving) CircularProgressIndicator(Modifier.padding(2.dp), strokeWidth = 2.dp) else Text("Speichern")
                    }
                },
            )
        },
    ) { padding ->
        Column(
            Modifier.fillMaxSize().padding(padding).verticalScroll(rememberScrollState()).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            vm.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }

            Card("Charakter") {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    IntField("Level", build.level, 1..BuildOptions.LEVEL_MAX, { build = build.copy(level = it) }, Modifier.weight(1f))
                    Column(Modifier.weight(1f)) {
                        Label("Sternbild")
                        Dropdown("C${build.constellation}", (0..6).map { "C$it" }, { build = build.copy(constellation = it.drop(1).toInt()) })
                    }
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    val t = build.talents
                    val max = BuildOptions.TALENT_MAX
                    IntField("Angriff", t.attack, 1..max, { build = build.copy(talents = t.copy(attack = it)) }, Modifier.weight(1f))
                    IntField("Skill", t.skill, 1..max, { build = build.copy(talents = t.copy(skill = it)) }, Modifier.weight(1f))
                    IntField("Burst", t.burst, 1..max, { build = build.copy(talents = t.copy(burst = it)) }, Modifier.weight(1f))
                }
            }

            Card("Waffe") {
                var picking by remember { mutableStateOf(false) }
                OutlinedButton(onClick = { picking = true }, Modifier.fillMaxWidth()) {
                    Text(build.weapon.ifBlank { "Waffe wählen" })
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    IntField("Level", build.weaponLevel, 1..BuildOptions.LEVEL_MAX, { build = build.copy(weaponLevel = it) }, Modifier.weight(1f))
                    Column(Modifier.weight(1f)) {
                        Label("Veredelung")
                        Dropdown("R${build.refinement}", (1..5).map { "R$it" }, { build = build.copy(refinement = it.drop(1).toInt()) })
                    }
                }
                if (picking) {
                    // Nur Waffen des passenden Typs, seltene zuerst
                    val weapons = vm.stammdaten.stammdaten.weapons
                        .filter { character == null || it.weaponType == character.weaponType }
                        .sortedWith(compareByDescending<de.sonictriplex.genshinteams.data.Weapon> { it.rarity }.thenBy { it.name })
                        .map { PickerItem(it.name, "${it.rarity} ★ · ${it.weaponType}") }
                    SearchPickerDialog(
                        "Waffe wählen", weapons, vm.stammdaten, "Keine Waffe",
                        onPick = { build = build.copy(weapon = it); picking = false },
                        onDismiss = { picking = false },
                    )
                }
            }

            Card("Artefaktsets") {
                SetPicker("Set 1", build.artifact, vm) { build = build.copy(artifact = it) }
                SetPicker("Set 2 (optional, bei 2er-Sets)", build.artifact2, vm) { build = build.copy(artifact2 = it) }
            }

            ARTIFACT_SLOTS.forEach { slotName ->
                val slot = build.artifactStats.getValue(slotName)
                Card(slotName) {
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                        IntField("Level", slot.level, 0..20, { v -> build = build.withSlot(slotName) { it.copy(level = v) } }, Modifier.weight(1f))
                        Dropdown(slot.rarity, BuildOptions.RARITIES, { v -> build = build.withSlot(slotName) { it.copy(rarity = v) } }, Modifier.weight(1f))
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                        Dropdown(
                            slot.mainStat, BuildOptions.MAIN_STATS.getValue(slotName),
                            { v -> build = build.withSlot(slotName) { it.copy(mainStat = v) } }, Modifier.weight(2f),
                        )
                        OutlinedTextField(
                            slot.mainValue, { v -> build = build.withSlot(slotName) { it.copy(mainValue = v) } },
                            label = { Text("Wert") }, singleLine = true, modifier = Modifier.weight(1f),
                        )
                    }
                    Label("Substats")
                    slot.substats.forEachIndexed { i, sub ->
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                            Dropdown(
                                sub.stat.ifBlank { BuildOptions.NONE }, listOf(BuildOptions.NONE) + BuildOptions.SUBSTATS,
                                { v ->
                                    val stat = if (v == BuildOptions.NONE) "" else v
                                    build = build.withSlot(slotName) { s -> s.withSubstat(i) { it.copy(stat = stat) } }
                                },
                                Modifier.weight(2f),
                            )
                            OutlinedTextField(
                                sub.value, { v -> build = build.withSlot(slotName) { s -> s.withSubstat(i) { it.copy(value = v) } } },
                                label = { Text("Wert") }, singleLine = true, modifier = Modifier.weight(1f),
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun SetPicker(label: String, value: String, vm: AppViewModel, onPick: (String) -> Unit) {
    var picking by remember { mutableStateOf(false) }
    Label(label)
    OutlinedButton(onClick = { picking = true }, Modifier.fillMaxWidth()) { Text(value.ifBlank { "Kein Set" }) }
    if (picking) {
        val sets = vm.stammdaten.stammdaten.artifacts.map { PickerItem(it.name) }
        SearchPickerDialog(
            "Artefaktset wählen", sets, null, "Kein Set",
            onPick = { onPick(it); picking = false },
            onDismiss = { picking = false },
        )
    }
}

@Composable
private fun Label(text: String) = Text(text, style = MaterialTheme.typography.labelMedium)

@Composable
private fun Card(title: String, content: @Composable () -> Unit) {
    androidx.compose.material3.Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(MaterialTheme.colorScheme.surface)) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(title, style = MaterialTheme.typography.titleSmall, color = MaterialTheme.colorScheme.primary)
            content()
        }
    }
}
