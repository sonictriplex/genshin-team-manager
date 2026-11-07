package de.sonictriplex.genshinteams.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/** Prüft den Client gegen die Referenzdateien aus shared/ (gleiche Dateien wie Desktop und Web). */
class ExchangeFormatTest {
    private val shared = File(System.getProperty("shared.dir"))

    @Test
    fun beispielDateiWirdGelesen() {
        val file = parseExchange(File(shared, "testdata/export-beispiel.json").readText())
        assertEquals(2, file.builds.size)
        assertEquals(listOf("Nilou", "Barbara"), file.teams.first().members)

        val nilou = file.builds.first { it.name == "Nilou" }
        assertEquals(9, nilou.talents.skill)
        assertEquals("Eisenstich", nilou.weapon)
        val blume = nilou.artifactStats.getValue("Blume")
        assertEquals("LP (Fix)", blume.mainStat)
        assertEquals(4, blume.substats.size)
        assertEquals("15,7", blume.substats[1].value)
    }

    @Test
    fun fremdeOderNeuereDateienWerdenAbgelehnt() {
        assertThrows(IllegalArgumentException::class.java) {
            parseExchange("""{"format":"anderes","version":1,"builds":[],"teams":[]}""")
        }
        assertThrows(IllegalArgumentException::class.java) {
            parseExchange("""{"format":"genshin-team-manager","version":99,"builds":[],"teams":[]}""")
        }
    }

    @Test
    fun stammdatenSindLesbarUndIconPfadePassen() {
        val data = AppJson.decodeFromString<Stammdaten>(File(shared, "stammdaten.json").readText())
        assertTrue(data.characters.size >= 100)
        assertTrue(data.weapons.isNotEmpty() && data.artifacts.isNotEmpty())
        // Jeder angegebene icon_path zeigt auf eine vorhandene Datei in shared/
        val paths = data.characters.mapNotNull { it.iconPath } + data.weapons.mapNotNull { it.iconPath }
        paths.forEach { assertTrue("fehlt: $it", File(shared, it).exists()) }
    }

    @Test
    fun iconPfadRegelEntsprichtDenAnderenClients() {
        assertEquals("assets/images/hu_tao.png", iconPathFor("Hu Tao"))
        assertEquals("assets/images/traveler.png", iconPathFor("Traveler (Dendro)"))
        assertEquals("assets/images/kaedehara_kazuha.png", iconPathFor("Kaedehara Kazuha"))
    }
}
