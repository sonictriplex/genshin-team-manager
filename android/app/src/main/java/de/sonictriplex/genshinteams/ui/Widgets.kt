package de.sonictriplex.genshinteams.ui

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.produceState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import de.sonictriplex.genshinteams.data.StammdatenRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/** Icon eines Charakters/einer Waffe aus den Assets; ohne Bild erscheint der erste Buchstabe. */
@Composable
fun NameIcon(name: String, repo: StammdatenRepository, size: Dp, modifier: Modifier = Modifier) {
    val image by produceState<ImageBitmap?>(null, name) {
        value = withContext(Dispatchers.IO) { repo.iconFor(name)?.asImageBitmap() }
    }
    val shape = RoundedCornerShape(8.dp)
    Box(
        modifier.size(size).clip(shape).background(MaterialTheme.colorScheme.surfaceVariant),
        contentAlignment = Alignment.Center,
    ) {
        val bmp = image
        if (bmp != null) {
            Image(bmp, contentDescription = name, contentScale = ContentScale.Crop, modifier = Modifier.size(size))
        } else {
            Text(name.take(1), fontSize = (size.value / 2).sp)
        }
    }
}
