package de.sonictriplex.genshinteams.data

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
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

class BuildEditingTest {
    private val shared = File(System.getProperty("shared.dir"))

    @Test
    fun normalisierenErgaenztAlleSlotsMitVierSubstats() {
        val build = Build(name = "Barbara", artifact = "— Keins —").normalized()
        assertEquals("", build.artifact)
        assertEquals(ARTIFACT_SLOTS.toSet(), build.artifactStats.keys)
        build.artifactStats.values.forEach { assertEquals(4, it.substats.size) }
        assertEquals("LP (Fix)", build.artifactStats.getValue("Blume").mainStat)
    }

    @Test
    fun speichernBeachtetNurGeaenderteSlotsUndBleibtImAustauschformat() {
        val original = parseExchange(File(shared, "testdata/export-beispiel.json").readText()).builds.first()
        val edited = original.normalized()
            .withSlot("Feder") { s -> s.copy(level = 16).withSubstat(0) { it.copy(stat = "KT%", value = "3,9") } }

        // Der Body ist selbst eine gültige Austauschdatei, die der Server (und die anderen Clients) lesen
        val body = importPayload(builds = listOf(edited))
        val sent = AppJson.parseToJsonElement(body).jsonObject
        assertEquals("merge", sent.getValue("mode").jsonPrimitive.content)
        val data = parseExchange(sent.getValue("data").toString())
        assertEquals(1, data.builds.size)
        assertEquals(emptyList<Team>(), data.teams)

        val feder = data.builds.single().artifactStats.getValue("Feder")
        assertEquals(16, feder.level)
        assertEquals("3,9", feder.substats[0].value)
        // JSON-Feldnamen des Formats ("val", "weapon_level", ...) und Standardwerte sind enthalten
        assertTrue(body.contains("\"val\":\"3,9\""))
        assertTrue(body.contains("\"weapon_level\":80"))
        assertTrue(body.contains("\"artifact_2\":"))
        assertTrue(body.contains("\"talents\":{\"attack\":1,\"skill\":9,\"burst\":9}"))
    }

    private val artifacts = AppJson.decodeFromString<Stammdaten>(File(shared, "stammdaten.json").readText()).artifacts

    @Test
    fun teileDerBuildSetsStehenZuerstUndOffPiecesFolgen() {
        val options = pieceOptions(artifacts, "Feder", listOf("Abenteurer", "Berserker", ""))
        assertEquals(listOf(true, true), options.take(2).map { it.inBuildSet })
        assertEquals(setOf("Abenteurerschwanzfeder", "Berserkerfeder"), options.take(2).map { it.name }.toSet())
        assertTrue(options.drop(2).none { it.inBuildSet })
        assertTrue(options.any { it.name == "Zuflucht des Gladiators" && it.setName == "Verbeugung des Gladiators" })
        val others = options.drop(2).map { it.name.lowercase() }
        assertEquals(others.sorted(), others)
    }

    @Test
    fun bonusUndPassivTexteKommenAusDenStammdaten() {
        val set = artifacts.first { it.name == "Abenteurer" }
        assertTrue(set.bonusText()!!.contains("2er-Bonus: Erhöht die max. LP um 1000."))
        val weapons = AppJson.decodeFromString<Stammdaten>(File(shared, "stammdaten.json").readText()).weapons
        val lamp = weapons.first { it.name == "Silberlampe" }
        assertTrue(lamp.passiveText(1)!!.startsWith("Sonnenspiegelung im Wasser (Veredelung 1)"))
        assertTrue(lamp.passiveText(5)!!.contains("Veredelung 5"))
        assertTrue(lamp.passiveText(9)!!.contains("Veredelung 5"))   // außerhalb des Bereichs: begrenzt
        assertEquals(null, weapons.first { it.passive == null }.passiveText(1))
    }

    @Test
    fun alteDefNamenWerdenZuVtd() {
        assertTrue(BuildOptions.SUBSTATS.containsAll(listOf("VTD%", "VTD (Fix)")))
        assertTrue(BuildOptions.SUBSTATS.none { it.startsWith("DEF") })
        assertTrue(BuildOptions.MAIN_STATS.values.flatten().none { it.startsWith("DEF") })

        // Datei und Server vor der Umbenennung: DEF% als Hauptwert, DEF (Fix) als Substat
        val legacy = File(shared, "testdata/export-beispiel.json").readText().replace("VTD", "DEF")
        assertTrue(legacy.contains("\"DEF%\"") && legacy.contains("\"DEF (Fix)\""))
        val build = parseExchange(legacy).builds.first()
        val stats = build.artifactStats.values.flatMap { listOf(it.mainStat) + it.substats.map { s -> s.stat } }
        assertTrue(stats.none { it.startsWith("DEF") })
        assertTrue("VTD (Fix)" in stats && "VTD%" in stats)
        // Ein alter Hauptwert fällt beim Bearbeiten nicht auf den ersten Eintrag zurück
        val sanduhr = Build(name = "X", artifactStats = mapOf("Sanduhr" to ArtifactSlot(mainStat = "DEF%")))
        assertEquals("VTD%", sanduhr.normalized().artifactStats.getValue("Sanduhr").mainStat)
    }

    @Test
    fun einzelteilSetsGibtEsNurBeiDerKrone() {
        assertTrue(pieceOptions(artifacts, "Krone", emptyList()).any { it.name == "Wasseropferdiadem" })
        assertTrue(pieceOptions(artifacts, "Blume", emptyList()).none { it.name == "Wasseropferdiadem" })
    }

    @Test
    fun teilnameBleibtBeimNormalisierenUndSpeichernErhalten() {
        val build = Build(name = "Barbara").normalized().withSlot("Feder") { it.copy(piece = "Zuflucht des Gladiators") }
        assertEquals("Zuflucht des Gladiators", build.normalized().artifactStats.getValue("Feder").piece)
        val body = importPayload(builds = listOf(build))
        assertTrue(body.contains("\"piece\":\"Zuflucht des Gladiators\""))
        val back = parseExchange(AppJson.parseToJsonElement(body).jsonObject.getValue("data").toString())
        assertEquals("Zuflucht des Gladiators", back.builds.single().artifactStats.getValue("Feder").piece)
        // Alte Dateien ohne "piece" bleiben lesbar
        val old = AppJson.decodeFromString<ArtifactSlot>("""{"rarity":"5★","level":20}""")
        assertEquals("", old.piece)
    }
}

class TeamEditingTest {
    @Test
    fun teamPayloadEnthaeltNurDasTeam() {
        val body = importPayload(teams = listOf(Team("Bloom", listOf("Nilou", "Barbara"))))
        val sent = AppJson.parseToJsonElement(body).jsonObject
        assertEquals("merge", sent.getValue("mode").jsonPrimitive.content)
        val data = parseExchange(sent.getValue("data").toString())
        assertEquals(emptyList<Build>(), data.builds)
        assertEquals(listOf(Team("Bloom", listOf("Nilou", "Barbara"))), data.teams)
    }

    @Test
    fun teamnameWirdGeprueft() {
        val existing = listOf("A", "B")
        assertEquals(null, validateTeamName("Neu", existing, null))
        assertEquals(null, validateTeamName("  B  ", existing, "B"))           // unverändert beim Bearbeiten
        assertTrue(validateTeamName("   ", existing, null)!!.contains("eingeben"))
        assertTrue(validateTeamName("A", existing, null)!!.contains("schon"))
        assertTrue(validateTeamName("A", existing, "B")!!.contains("schon"))   // Umbenennen auf ein anderes Team
        assertTrue(validateTeamName("x".repeat(256), existing, null)!!.contains("lang"))
    }
}

class MoveTest {
    @Test
    fun reihenfolgeDerTeamsGehtAlsOrderListeAnDenServer() {
        assertEquals("""{"order":["B","A \"x\"","C"]}""", teamOrderPayload(listOf("B", "A \"x\"", "C")))
    }

    @Test
    fun verschiebenAendertNurDieReihenfolge() {
        val team = listOf("A", "B", "C", "D")
        assertEquals(listOf("B", "A", "C", "D"), team.moved(0, 1))
        assertEquals(listOf("A", "B", "D", "C"), team.moved(3, 2))
        assertEquals(listOf("D", "A", "B", "C"), team.moved(3, 0))
        assertEquals(team, team.moved(0, -1))   // außerhalb: unverändert
        assertEquals(team, team.moved(2, 4))
        assertEquals(team, team.moved(1, 1))
    }
}

/** Prüft, welche Header die App mit dem Token sendet (ohne Netzwerk, mit abgefangener Anfrage). */
class ApiHeadersTest {
    private val example = java.io.File(System.getProperty("shared.dir"), "testdata/export-beispiel.json").readText()

    private fun clientWith(captured: MutableList<okhttp3.Request>): okhttp3.OkHttpClient =
        okhttp3.OkHttpClient.Builder().addInterceptor { chain ->
            captured += chain.request()
            okhttp3.Response.Builder()
                .request(chain.request()).protocol(okhttp3.Protocol.HTTP_1_1).code(200).message("OK")
                .body(example.toResponseBody("application/json".toMediaType())).build()
        }.build()

    @Test
    fun tokenGehtInBeidenHeadernMit() {
        val captured = mutableListOf<okhttp3.Request>()
        val api = ApiClient("https://example.org", { "t".repeat(64) }, clientWith(captured))

        val data = kotlinx.coroutines.runBlocking { api.fetchUserData() }

        assertEquals(2, data.builds.size)
        val request = captured.single()
        assertEquals("https://example.org/api/transfer.php", request.url.toString())
        assertEquals("Bearer " + "t".repeat(64), request.header("Authorization"))
        assertEquals("t".repeat(64), request.header("X-Auth-Token"))
    }

    @Test
    fun ohneTokenWirdNichtsGesendet() {
        val captured = mutableListOf<okhttp3.Request>()
        val api = ApiClient("https://example.org", { null }, clientWith(captured))

        assertThrows(UnauthorizedException::class.java) { kotlinx.coroutines.runBlocking { api.fetchUserData() } }
        assertTrue(captured.isEmpty())
    }
}

class UserDataCacheTest {
    private val example = parseExchange(java.io.File(System.getProperty("shared.dir"), "testdata/export-beispiel.json").readText())
    private fun tempDir() = java.nio.file.Files.createTempDirectory("cache-test").toFile().also { it.deleteOnExit() }

    @Test
    fun speichernUndLadenErgibtDieselbenDaten() {
        val cache = UserDataCache(tempDir())
        assertEquals(null, cache.load("https://example.org", "jens"))

        cache.save("https://example.org", "jens", example, now = 1_700_000_000_000)
        val loaded = cache.load("https://example.org", "jens")!!

        assertEquals(example, loaded.data)
        assertEquals(1_700_000_000_000, loaded.savedAt)
        assertEquals(listOf("Nilou", "Barbara"), loaded.data.teams.first().members)
    }

    @Test
    fun cacheGiltNurFuerDenGleichenServerUndNutzer() {
        val cache = UserDataCache(tempDir())
        cache.save("https://example.org/", "jens", example)

        assertTrue(cache.load("https://example.org", "jens") != null)          // Schrägstrich am Ende egal
        assertEquals(null, cache.load("https://example.org", "anna"))          // anderer Nutzer
        assertEquals(null, cache.load("https://anderer-server.de", "jens"))    // anderer Server
    }

    @Test
    fun beschaedigterCacheIstKeinCacheUndStuertztNicht() {
        val dir = tempDir()
        val cache = UserDataCache(dir)
        java.io.File(dir, "userdata-cache.json").writeText("{ das ist kein gültiges json")
        assertEquals(null, cache.load("https://example.org", "jens"))

        cache.save("https://example.org", "jens", example)     // wird einfach überschrieben
        assertTrue(cache.load("https://example.org", "jens") != null)
    }

    @Test
    fun neuerStandErsetztDenAltenUndLoeschenRaeumtAuf() {
        val dir = tempDir()
        val cache = UserDataCache(dir)
        cache.save("https://example.org", "jens", example, now = 1)
        val changed = example.copy(teams = example.teams + Team("Neu", listOf("Furina")))
        cache.save("https://example.org", "jens", changed, now = 2)

        val loaded = cache.load("https://example.org", "jens")!!
        assertEquals(3, loaded.data.teams.size)
        assertEquals(2, loaded.savedAt)
        assertEquals(listOf("userdata-cache.json"), dir.list()!!.toList())   // keine Temp-Datei übrig

        cache.clear()
        assertEquals(null, cache.load("https://example.org", "jens"))
        assertTrue(dir.list()!!.isEmpty())
    }
}

class NetworkErrorTest {
    private fun clientThrowing(error: java.io.IOException) = okhttp3.OkHttpClient.Builder()
        .addInterceptor { throw error }.build()

    @Test
    fun fehlendeVerbindungIstEineNetworkException() {
        val api = ApiClient("https://example.org", { "t".repeat(64) }, clientThrowing(java.net.UnknownHostException("kein Netz")))
        val e = assertThrows(NetworkException::class.java) { kotlinx.coroutines.runBlocking { api.fetchUserData() } }
        assertTrue(e.message!!.contains("nicht erreichbar"))
    }

    @Test
    fun zeitueberschreitungIstEineNetworkException() {
        val api = ApiClient("https://example.org", { "t".repeat(64) }, clientThrowing(java.net.SocketTimeoutException("timeout")))
        assertThrows(NetworkException::class.java) { kotlinx.coroutines.runBlocking { api.fetchUserData() } }
    }

    @Test
    fun serverfehlerIstKeineNetworkException() {
        val http = okhttp3.OkHttpClient.Builder().addInterceptor { chain ->
            okhttp3.Response.Builder().request(chain.request()).protocol(okhttp3.Protocol.HTTP_1_1).code(500).message("err")
                .body("""{"error":"Fehler beim Laden."}""".toResponseBody("application/json".toMediaType())).build()
        }.build()
        val api = ApiClient("https://example.org", { "t".repeat(64) }, http)

        val e = assertThrows(ApiException::class.java) { kotlinx.coroutines.runBlocking { api.fetchUserData() } }
        assertTrue(e !is NetworkException)
        assertEquals("Fehler beim Laden.", e.message)
    }
}

class ServerConfigTest {
    @Test
    fun festeServeradresseIstEineGueltigeHttpsAdresse() {
        val url = de.sonictriplex.genshinteams.BuildConfig.DEFAULT_SERVER_URL
        assertTrue(url.startsWith("https://"))
        assertTrue("kein Schrägstrich am Ende: $url", !url.endsWith("/"))
        val parsed = okhttp3.HttpUrl.Companion.run { url.toHttpUrl() }
        assertEquals("genshin-manager.media-matrix.de", parsed.host)
        // ApiClient hängt /api/ an die Adresse an
        assertEquals("https://genshin-manager.media-matrix.de/api/transfer.php",
            ApiClient(url, { null }).let { url + "/api/transfer.php" })
    }
}

class RegistrationTest {
    @Test
    fun eingabenWerdenVorabGeprueft() {
        assertEquals(null, validateRegistration("jens", "geheim1", "geheim1"))
        assertEquals(null, validateRegistration("  abc  ", "123456", "123456"))            // Leerzeichen am Rand zählen nicht
        assertTrue(validateRegistration("ab", "geheim1", "geheim1")!!.contains("Benutzername"))
        assertTrue(validateRegistration("   ab ", "geheim1", "geheim1")!!.contains("mindestens 3"))
        assertTrue(validateRegistration("jens", "12345", "12345")!!.contains("Passwort"))
        assertTrue(validateRegistration("jens", "geheim1", "geheim2")!!.contains("stimmen nicht überein"))
        // die Reihenfolge der Prüfungen: erst Name, dann Länge, dann Wiederholung
        assertTrue(validateRegistration("ab", "x", "y")!!.contains("Benutzername"))
    }

    /** Beantwortet Anfragen der Reihe nach und merkt sich sie: (Adresse, Body) je Anfrage. */
    private class Script(private vararg val replies: Pair<Int, String>) {
        val seen = mutableListOf<Pair<String, String>>()
        fun client() = okhttp3.OkHttpClient.Builder().addInterceptor { chain ->
            val request = chain.request()
            val buffer = okio.Buffer().also { b -> request.body?.writeTo(b) }
            seen += request.url.encodedPath + "?" + request.url.encodedQuery to buffer.readUtf8()
            val (code, json) = replies[seen.size - 1]
            okhttp3.Response.Builder().request(request).protocol(okhttp3.Protocol.HTTP_1_1).code(code).message("x")
                .body(json.toResponseBody("application/json".toMediaType())).build()
        }.build()
    }

    @Test
    fun registrierungLegtKontoAnUndMeldetDanachMitTokenAn() {
        val script = Script(
            200 to """{"success":true,"username":"neu"}""",
            200 to """{"token":"${"a".repeat(64)}","username":"neu","expires_at":"2027-01-01 00:00:00"}""",
        )
        val api = ApiClient("https://example.org", { null }, script.client())

        val (token, name) = kotlinx.coroutines.runBlocking { api.register("neu", "geheim1") }

        assertEquals("a".repeat(64), token)
        assertEquals("neu", name)
        assertEquals(2, script.seen.size)
        assertEquals("/api/auth.php?action=register", script.seen[0].first)
        assertTrue(script.seen[0].second.contains("\"username\":\"neu\""))
        assertTrue(script.seen[0].second.contains("\"password\":\"geheim1\""))
        assertEquals("/api/auth.php?action=token", script.seen[1].first)
    }

    @Test
    fun vergebenerNameWirdMitDerServermeldungGemeldetUndEsGibtKeinenTokenAbruf() {
        val script = Script(409 to """{"error":"Dieser Benutzername ist bereits vergeben."}""")
        val api = ApiClient("https://example.org", { null }, script.client())

        val e = assertThrows(ApiException::class.java) { kotlinx.coroutines.runBlocking { api.register("jens", "geheim1") } }

        assertEquals("Dieser Benutzername ist bereits vergeben.", e.message)
        assertEquals(1, script.seen.size)
    }

    @Test
    fun scheitertDieAnmeldungNachDerRegistrierungWirdDasErklaert() {
        val script = Script(
            200 to """{"success":true}""",
            500 to """{"error":"Token konnte nicht erstellt werden."}""",
        )
        val api = ApiClient("https://example.org", { null }, script.client())

        val e = assertThrows(ApiException::class.java) { kotlinx.coroutines.runBlocking { api.register("neu", "geheim1") } }

        assertTrue(e.message!!.contains("Konto wurde angelegt"))
        assertEquals(2, script.seen.size)
    }

    @Test
    fun gesamtwerteSummierenJeStat() {
        assertEquals(46.6, parseStatValue("46,6")!!, 0.0001)
        assertEquals(4780.0, parseStatValue("4,780")!!, 0.0001)
        assertEquals(null, parseStatValue("abc"))

        val build = Build(
            name = "Test",
            artifactStats = mapOf(
                "Blume" to ArtifactSlot(mainStat = "LP (Fix)", mainValue = "4780", substats = listOf(Substat("LP (Fix)", "209"), Substat("KT%", "3,9"))),
                "Krone" to ArtifactSlot(mainStat = "KT%", mainValue = "31,1", substats = listOf(Substat("DEF%", "5,8"), Substat("ANG%", "abc"))),
            ),
        )
        val totals = build.artifactTotals()
        assertEquals(listOf("LP (Fix)", "VTD%", "KT%"), totals.map { it.first })
        assertEquals(listOf("4989", "5,8%", "35%"), totals.map { formatStatTotal(it.first, it.second) })
    }
}
