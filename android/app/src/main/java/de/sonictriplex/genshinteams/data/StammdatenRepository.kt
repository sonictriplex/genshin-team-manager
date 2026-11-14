package de.sonictriplex.genshinteams.data

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory


/** Stammdaten und Bilder aus den Assets (Quelle: shared/ im Monorepo). */
class StammdatenRepository(private val context: Context) {

    val stammdaten: Stammdaten by lazy {
        val text = context.assets.open("stammdaten.json").bufferedReader(Charsets.UTF_8).use { it.readText() }
        AppJson.decodeFromString<Stammdaten>(text)
    }

    private val charactersByName by lazy { stammdaten.characters.associateBy { it.name } }
    private val weaponsByName by lazy { stammdaten.weapons.associateBy { it.name } }

    fun character(name: String): Character? = charactersByName[name]
    fun weapon(name: String): Weapon? = weaponsByName[name]

    /** Lädt das Icon eines Charakters, einer Waffe oder eines Artefaktteils, oder null, wenn es keins gibt. */
    fun iconFor(name: String): Bitmap? {
        val explicit = character(name)?.iconPath ?: weapon(name)?.iconPath
        // Fehlt die angegebene Datei, gilt wie im Desktop die Namensregel als Rückfall
        return explicit?.let(::loadBitmap)
            ?: loadBitmap(iconPathFor(name, "characters")) ?: loadBitmap(iconPathFor(name, "weapons"))
            ?: loadBitmap(iconPathFor(name, "weapons", keepHyphen = false))
            ?: loadBitmap(iconPathFor(name, "artifacts")) ?: loadBitmap(iconPathFor(name, "artifacts", keepHyphen = false))
    }

    /** Lädt ein beliebiges Bild aus den Assets (z. B. `assets/images/ui/mm_logo.png`), oder null. */
    fun loadBitmap(path: String): Bitmap? = try {
        context.assets.open(path).use { BitmapFactory.decodeStream(it) }
    } catch (_: java.io.IOException) {
        null
    }
}

/**
 * Leitet den Icon-Pfad aus einem Namen ab (wie Desktop und Web): Kleinbuchstaben, Leerzeichen und
 * Bindestriche werden zu "_", Apostrophe/Anführungszeichen fallen weg, Klammerzusätze ebenfalls.
 */
fun iconPathFor(name: String, kind: String = "characters", keepHyphen: Boolean = true): String {
    var clean = name.substringBefore("(").trim().lowercase()
    for (ch in listOf("'", "’", "„", "“")) clean = clean.replace(ch, "")
    // Manche Dateien heißen ohne Bindestrich-Unterstrich ("Homa-Stab" -> homastab.png, wie im Web)
    clean = clean.replace(" ", "_").replace("-", if (keepHyphen) "_" else "")
    return "assets/images/$kind/$clean.png"
}
