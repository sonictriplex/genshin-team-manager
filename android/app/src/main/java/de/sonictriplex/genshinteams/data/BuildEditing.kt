package de.sonictriplex.genshinteams.data

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

/** Body für `POST api/transfer.php`: genau ein Build, Modus "merge", Teams bleiben unberührt. */
fun buildImportPayload(build: Build): String = SaveJson.encodeToString(
    ImportRequest.serializer(),
    ImportRequest("merge", ExchangeFile(EXCHANGE_FORMAT, EXCHANGE_VERSION, builds = listOf(build))),
)

@kotlinx.serialization.Serializable
data class ImportRequest(val mode: String, val data: ExchangeFile)

@kotlinx.serialization.Serializable
data class ImportResponse(val builds: Int = 0, val teams: Int = 0, val skipped: List<String> = emptyList())
