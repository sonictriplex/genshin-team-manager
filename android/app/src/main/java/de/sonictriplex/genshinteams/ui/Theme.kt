package de.sonictriplex.genshinteams.ui

import android.graphics.BitmapFactory
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.getValue
import androidx.compose.runtime.produceState
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily

/** Farbpalette wie in der Desktop-Version (desktop/styles.py) und der Web-Version (web/index.html). */
object Palette {
    val BgWindow = Color(0xFF0D0B14)
    val BgPanel = Color(0xFF1A1825)
    val BgInput = Color(0xFF12101B)
    val BgHover = Color(0xFF252136)
    val Border = Color(0xFF332D47)
    val Accent = Color(0xFF5BC0BE)
    val Gold = Color(0xFFD89F53)
    val Epic = Color(0xFFA561C9)
    val Danger = Color(0xFFFF7A5C)
    val Text = Color(0xFFE1E1E6)
    val TextSoft = Color(0xFFB9B7CC)
}

private val GenshinColors = darkColorScheme(
    primary = Palette.Accent,
    onPrimary = Palette.BgInput,
    primaryContainer = Palette.Accent,          // u. a. der Knopf "Neues Team"
    onPrimaryContainer = Palette.BgInput,
    secondary = Palette.Accent,
    tertiary = Palette.Gold,
    background = Color.Transparent,             // Scaffolds zeigen das Hintergrundbild (siehe AppBackground)
    onBackground = Palette.Text,
    surface = Palette.BgPanel,
    onSurface = Palette.Text,
    surfaceVariant = Palette.BgHover,
    onSurfaceVariant = Palette.TextSoft,
    outline = Color(0xFF6A6483),
    outlineVariant = Palette.Border,
    error = Palette.Danger,
)

/** Wie Desktop und Web immer dunkel; Überschriften in der Genshin-Schrift (shared/assets/zh-cn.ttf). */
@Composable
fun GenshinTheme(content: @Composable () -> Unit) {
    val assets = LocalContext.current.assets
    val genshin = remember { FontFamily(Font("assets/zh-cn.ttf", assets)) }
    val base = Typography()
    val typography = remember(genshin) {
        base.copy(
            headlineMedium = base.headlineMedium.copy(fontFamily = genshin),
            titleLarge = base.titleLarge.copy(fontFamily = genshin),
            titleMedium = base.titleMedium.copy(fontFamily = genshin),
            titleSmall = base.titleSmall.copy(fontFamily = genshin),
        )
    }
    MaterialTheme(colorScheme = GenshinColors, typography = typography, content = content)
}

/** Elementfarben der anderen Clients. */
fun elementColor(element: String): Color = when (element) {
    "Pyro" -> Color(0xFFDF4A28)
    "Hydro" -> Color(0xFF2393C1)
    "Anemo" -> Color(0xFF23C197)
    "Electro", "Elektro" -> Color(0xFF9643DB)
    "Dendro" -> Color(0xFF26BB3A)
    "Cryo", "Kryo" -> Color(0xFF62C8DB)
    "Geo" -> Color(0xFFCBA128)
    else -> Color(0xFF8A889E)
}

/** Rahmenfarbe nach Seltenheit: 5★ golden, 4★ violett. */
fun rarityColor(rarity: Int): Color = when (rarity) {
    5 -> Palette.Gold
    4 -> Palette.Epic
    3 -> Color(0xFF5B8FD9)
    else -> Color(0xFF8A889E)
}

/**
 * Vollbild-Hintergrund wie in der Web-Version (shared/assets/images/genshin-impact.jpg, zugeschnitten wie
 * `background-size: cover`), mit dunkler Abdeckung für die Lesbarkeit. Vor dem Laden bleibt es einfarbig.
 */
@Composable
fun AppBackground(content: @Composable () -> Unit) {
    val context = LocalContext.current
    val image by produceState<ImageBitmap?>(null) {
        value = withContext(Dispatchers.IO) {
            try {
                // Das Bild ist 2752×1536 px; auf Handygröße verkleinert laden spart Speicher
                val opts = BitmapFactory.Options().apply { inSampleSize = 2 }
                context.assets.open("assets/images/genshin-impact.jpg").use { BitmapFactory.decodeStream(it, null, opts) }?.asImageBitmap()
            } catch (_: java.io.IOException) {
                null
            }
        }
    }
    Box(Modifier.fillMaxSize().background(Palette.BgWindow)) {
        image?.let {
            Image(it, contentDescription = null, contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize())
            Box(Modifier.fillMaxSize().background(Palette.BgWindow.copy(alpha = 0.45f)))
        }
        content()
    }
}
