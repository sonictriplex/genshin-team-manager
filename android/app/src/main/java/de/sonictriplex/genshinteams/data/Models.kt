package de.sonictriplex.genshinteams.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

/** JSON-Konfiguration für alle Dateien: unbekannte Felder (neuere Versionen) werden ignoriert. */
val AppJson = Json {
    ignoreUnknownKeys = true
    coerceInputValues = true
    explicitNulls = false
}

// --- Stammdaten (shared/stammdaten.json) ---

@Serializable
data class Stammdaten(
    val characters: List<Character> = emptyList(),
    val weapons: List<Weapon> = emptyList(),
    val artifacts: List<ArtifactSet> = emptyList(),
)

@Serializable
data class Character(
    val name: String,
    val element: String = "",
    @SerialName("weapon_type") val weaponType: String = "",
    val region: String = "",
    val rarity: Int = 4,
    @SerialName("icon_path") val iconPath: String? = null,
)

@Serializable
data class Weapon(
    val name: String,
    @SerialName("weapon_type") val weaponType: String = "",
    val rarity: Int = 4,
    @SerialName("icon_path") val iconPath: String? = null,
    /** Passiv der Waffe; null bei Waffen ohne (z. B. Anfängerwaffen). */
    val passive: WeaponPassive? = null,
)

/** Beschreibung des Waffen-Passivs: [text] hat je einen Eintrag für Veredelung 1 bis 5. */
@Serializable
data class WeaponPassive(val name: String = "", val text: List<String> = emptyList())

@Serializable
data class ArtifactSet(
    val name: String,
    @SerialName("bonus_1pc") val bonus1pc: String = "",
    @SerialName("bonus_2pc") val bonus2pc: String = "",
    @SerialName("bonus_4pc") val bonus4pc: String = "",
    /** Namen der Teile je Slot (Blume, Feder, ...); 1er-Sets haben nur die Krone. */
    val pieces: Map<String, String> = emptyMap(),
)

// --- Austauschformat (shared/exchange-format.md) ---

const val EXCHANGE_FORMAT = "genshin-team-manager"
const val EXCHANGE_VERSION = 1

@Serializable
data class ExchangeFile(
    val format: String,
    val version: Int,
    @SerialName("exported_at") val exportedAt: String? = null,
    val builds: List<Build> = emptyList(),
    val teams: List<Team> = emptyList(),
)

@Serializable
data class Build(
    val name: String,
    val level: Int = 90,
    val constellation: Int = 0,
    val weapon: String = "",
    @SerialName("weapon_level") val weaponLevel: Int = 90,
    val refinement: Int = 1,
    val artifact: String = "",
    @SerialName("artifact_2") val artifact2: String = "",
    val talents: Talents = Talents(),
    @SerialName("artifact_stats") val artifactStats: Map<String, ArtifactSlot> = emptyMap(),
)

@Serializable
data class Talents(val attack: Int = 1, val skill: Int = 1, val burst: Int = 1)

@Serializable
data class ArtifactSlot(
    /** Name des Artefaktteils (z. B. "Zuflucht des Gladiators"); leer = nicht gewählt. */
    val piece: String = "",
    val rarity: String = "",
    val level: Int = 0,
    @SerialName("main_stat") val mainStat: String = "",
    @SerialName("main_value") val mainValue: String = "",
    val substats: List<Substat> = emptyList(),
)

@Serializable
data class Substat(
    val stat: String = "",
    // Im JSON heißt das Feld "val", was in Kotlin ein Schlüsselwort ist
    @SerialName("val") val value: String = "",
)

@Serializable
data class Team(val name: String, val members: List<String> = emptyList())

/** Reihenfolge der Artefakt-Slots in der Oberfläche. */
val ARTIFACT_SLOTS = listOf("Blume", "Feder", "Sanduhr", "Kelch", "Krone")

/** Vor der Umbenennung gespeicherte Stats: DEF heißt jetzt VTD (Verteidigung). */
private val LEGACY_STAT_NAMES = mapOf("DEF%" to "VTD%", "DEF (Fix)" to "VTD (Fix)")

fun currentStatName(stat: String): String = LEGACY_STAT_NAMES[stat] ?: stat

/** Wandelt alte Stat-Namen in Haupt- und Substats aller Slots um. */
fun Build.withCurrentStatNames(): Build = copy(
    artifactStats = artifactStats.mapValues { (_, slot) ->
        slot.copy(
            mainStat = currentStatName(slot.mainStat),
            substats = slot.substats.map { it.copy(stat = currentStatName(it.stat)) },
        )
    },
)

/** Liest eine Export-Datei und prüft Format und Version wie die anderen Clients. */
fun parseExchange(text: String): ExchangeFile {
    val file = AppJson.decodeFromString<ExchangeFile>(text)
    require(file.format == EXCHANGE_FORMAT) { "Die Datei ist keine Export-Datei des Genshin Team-Managers." }
    require(file.version <= EXCHANGE_VERSION) { "Die Datei stammt aus einer neueren Version und kann nicht gelesen werden." }
    return file.copy(builds = file.builds.map { it.withCurrentStatNames() })
}
