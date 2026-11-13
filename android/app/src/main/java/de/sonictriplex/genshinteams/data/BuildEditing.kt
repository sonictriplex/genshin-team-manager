package de.sonictriplex.genshinteams.data

import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.Json

/** Auswahllisten der Build-Bearbeitung (identisch zu web/index.html und desktop/widgets.py). */
object BuildOptions {
    const val NONE = "— Keiner —"
    val RARITIES = listOf("5★", "4★")
    val SUBSTATS = listOf(
        "KT%", "KSCH%", "ANG%", "ANG (Fix)", "LP%", "LP (Fix)", "DEF%", "DEF (Fix)", "Elementarkunde", "Aufladerate",
    )
    val MAIN_STATS: Map<String, List<String>> = mapOf(
        "Blume" to listOf("LP (Fix)"),
        "Feder" to listOf("ANG (Fix)"),
        "Sanduhr" to listOf("ANG%", "LP%", "DEF%", "Elementarkunde", "Aufladerate"),
        "Kelch" to listOf(
            "Pyro-SCH-Bonus%", "Hydro-SCH-Bonus%", "Kryo-SCH-Bonus%", "Elektro-SCH-Bonus%", "Anemo-SCH-Bonus%",
            "Geo-SCH-Bonus%", "Dendro-SCH-Bonus%", "Physischer SCH-Bonus%", "ANG%", "LP%", "DEF%", "Elementarkunde",
        ),
        "Krone" to listOf("KT%", "KSCH%", "ANG%", "LP%", "DEF%", "Heilungsbonus%", "Elementarkunde"),
    )

    const val LEVEL_MAX = 90
    const val TALENT_MAX = 13
}

/** Platzhalter wie "— Zweites 2er-Set (optional) —" gelten als "nichts gewählt". */
fun isPlaceholder(value: String) = value.isBlank() || value.startsWith("—")

/**
 * Bringt einen Build in die Form für die Bearbeitung: alle fünf Artefakt-Slots vorhanden, je 4 Substats,
 * Hauptwert aus der erlaubten Liste (wie die Web-Version, die immer alle Slots speichert).
 */
fun Build.normalized(): Build = copy(
    artifact = if (isPlaceholder(artifact)) "" else artifact,
    artifact2 = if (isPlaceholder(artifact2)) "" else artifact2,
    artifactStats = ARTIFACT_SLOTS.associateWith { slotName ->
        val mains = BuildOptions.MAIN_STATS.getValue(slotName)
        val slot = artifactStats[slotName] ?: ArtifactSlot(rarity = "5★", level = 20)
        slot.copy(
            rarity = slot.rarity.ifBlank { "5★" },
            mainStat = slot.mainStat.takeIf { it in mains } ?: mains.first(),
            substats = (slot.substats + List(4) { Substat() }).take(4),
        )
    },
)

/** Beschreibung des Passivs bei der gegebenen Veredelung (1–5), oder null, wenn die Waffe keins hat. */
fun Weapon.passiveText(refinement: Int): String? {
    val texts = passive?.text?.takeIf { it.isNotEmpty() } ?: return null
    val step = refinement.coerceIn(1, texts.size)
    return "${passive.name} (Veredelung $step)\n\n${texts[step - 1]}"
}

/** Set-Boni (1er, 2er, 4er) als Text, oder null, wenn das Set keine Beschreibung hat. */
fun ArtifactSet.bonusText(): String? {
    val parts = listOf("1er" to bonus1pc, "2er" to bonus2pc, "4er" to bonus4pc)
        .filter { it.second.isNotBlank() }.map { "${it.first}-Bonus: ${it.second}" }
    return parts.takeIf { it.isNotEmpty() }?.joinToString("\n\n")
}

/** Ein Eintrag der Teil-Auswahl: [inBuildSet] = das Teil gehört zu einem der beiden Sets des Builds. */
data class PieceOption(val name: String, val setName: String, val inBuildSet: Boolean)

/**
 * Auswahl für das Teil eines Slots: zuerst die Teile der Sets des Builds, danach die aller übrigen Sets
 * alphabetisch. So lässt sich auch ein Off-Piece (ein Teil aus einem anderen Set) wählen.
 */
fun pieceOptions(artifacts: List<ArtifactSet>, slotName: String, buildSets: List<String>): List<PieceOption> {
    val wanted = buildSets.filter { it.isNotBlank() }.toSet()
    val all = artifacts.mapNotNull { set ->
        set.pieces[slotName]?.takeIf { it.isNotBlank() }?.let { PieceOption(it, set.name, set.name in wanted) }
    }.distinctBy { it.name }
    return all.filter { it.inBuildSet } + all.filterNot { it.inBuildSet }.sortedBy { it.name.lowercase() }
}

fun Build.withSlot(slotName: String, change: (ArtifactSlot) -> ArtifactSlot): Build {
    val slot = artifactStats[slotName] ?: return this
    return copy(artifactStats = artifactStats + (slotName to change(slot)))
}

fun ArtifactSlot.withSubstat(index: Int, change: (Substat) -> Substat): ArtifactSlot =
    copy(substats = substats.mapIndexed { i, s -> if (i == index) change(s) else s })

/** JSON mit allen Feldern (auch Standardwerten), wie der Server sie erwartet. */
private val SaveJson = Json {
    encodeDefaults = true
    explicitNulls = false
}

/** Body für `POST api/transfer.php` im Modus "merge": nur die übergebenen Builds und Teams werden geschrieben. */
fun importPayload(builds: List<Build> = emptyList(), teams: List<Team> = emptyList()): String = SaveJson.encodeToString(
    ImportRequest.serializer(),
    ImportRequest("merge", ExchangeFile(EXCHANGE_FORMAT, EXCHANGE_VERSION, builds = builds, teams = teams)),
)

/** Anfrage an teams.php, die die Reihenfolge der Teams speichert: {"order": ["Team A", "Team B", ...]}. */
fun teamOrderPayload(names: List<String>): String =
    buildJsonObject { put("order", JsonArray(names.map { JsonPrimitive(it) })) }.toString()

/** Verschiebt das Element an Position [from] nach [to] (z. B. um die Reihenfolge im Team zu ändern). */
fun <T> List<T>.moved(from: Int, to: Int): List<T> {
    if (from !in indices || to !in indices || from == to) return this
    return toMutableList().apply { add(to, removeAt(from)) }
}

const val MAX_TEAM_SIZE = 4
const val MAX_TEAM_NAME = 255

/**
 * Prüft einen Teamnamen und gibt eine Fehlermeldung zurück, oder null wenn er gültig ist.
 * [original] ist der bisherige Name beim Bearbeiten (darf unverändert bleiben).
 */
fun validateTeamName(name: String, existing: List<String>, original: String?): String? {
    val trimmed = name.trim()
    return when {
        trimmed.isEmpty() -> "Bitte einen Teamnamen eingeben."
        trimmed.length > MAX_TEAM_NAME -> "Der Teamname ist zu lang."
        trimmed != original && trimmed in existing -> "Ein Team mit diesem Namen gibt es schon."
        else -> null
    }
}

@kotlinx.serialization.Serializable
data class ImportRequest(val mode: String, val data: ExchangeFile)

@kotlinx.serialization.Serializable
data class ImportResponse(val builds: Int = 0, val teams: Int = 0, val skipped: List<String> = emptyList())
