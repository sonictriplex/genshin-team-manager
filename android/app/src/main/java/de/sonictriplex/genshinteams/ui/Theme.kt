package de.sonictriplex.genshinteams.ui

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val Gold = Color(0xFFE0B65A)

private val Dark = darkColorScheme(
    primary = Gold,
    onPrimary = Color(0xFF1B1830),
    background = Color(0xFF1B1830),
    surface = Color(0xFF26233F),
    surfaceVariant = Color(0xFF322F52),
)
private val Light = lightColorScheme(primary = Color(0xFF7A5A12))

@Composable
fun GenshinTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = if (isSystemInDarkTheme()) Dark else Light, content = content)
}

/** Farbton je Element (wie in der Desktop-Version). */
fun elementColor(element: String): Color = when (element) {
    "Pyro" -> Color(0xFFE5533D)
    "Hydro" -> Color(0xFF3F8EF0)
    "Anemo" -> Color(0xFF4FC9A4)
    "Elektro", "Electro" -> Color(0xFFA568E6)
    "Dendro" -> Color(0xFF8BC53F)
    "Kryo", "Cryo" -> Color(0xFF7FD3E8)
    "Geo" -> Color(0xFFE0B65A)
    else -> Color(0xFF9A98B0)
}
