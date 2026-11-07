# Android-App

Online-Client für die Web-Version. Die App greift **nicht** direkt auf MySQL zu, sondern über die PHP-API in `../web/api/` (Anmeldung per Token, siehe `../web/README.md`).

**Stand:** Anmelden, Teamliste, Build-Ansicht sowie Bearbeiten und Speichern von Builds und Teams (anlegen, ändern, umbenennen, löschen) funktionieren.

## Technik

- Kotlin, Jetpack Compose (Material 3), Navigation Compose
- OkHttp und kotlinx.serialization für die API; Server-Adresse in app-privaten SharedPreferences, der Token verschlüsselt mit einem AES-Schlüssel aus dem Android Keystore (`TokenCipher`). Ist der Schlüssel ungültig, gilt man als abgemeldet; ein Klartext-Token aus Version 0.1 wird beim ersten Start verschlüsselt
- `minSdk` 26, `compileSdk` 37, Gradle 9.6 (Wrapper), Android Gradle Plugin 9.5

## Aussehen

Immer dunkel wie Desktop und Web (Palette aus `desktop/styles.py`). Überschriften in der Genshin-Schrift `shared/assets/zh-cn.ttf`, Charakterkarten mit Verlauf in der Elementfarbe und Rahmen nach Seltenheit (5★ golden, 4★ violett).

## Bearbeiten

Teams und Builds lassen sich bearbeiten; die Reihenfolge der Teammitglieder ändert man mit den Pfeilen unter den Icons. Beim Verlassen mit ungespeicherten Änderungen (Abbrechen oder Zurück) fragt die App nach.

## Gemeinsame Daten

`app/build.gradle.kts` bindet `../shared` als Asset-Ordner ein. Bilder (`assets/images/…`) und `stammdaten.json` liegen in der APK unter denselben Pfaden wie im Repo. Spezifikationen und Testdaten sind ausgeschlossen. Die Daten werden also nicht kopiert; neue Bilder oder Stammdaten wirken nach einem neuen Build.

Teams und Builds kommen über `api/transfer.php` im [Austauschformat](../shared/exchange-format.md). Beim Speichern sendet die App genau einen Build oder ein Team per `POST` im Modus `merge` an dieselbe Adresse; alles andere bleibt unberührt, und der Server begrenzt die Werte wie bei den anderen Clients. Teams löscht sie mit `DELETE api/teams.php?name=…`; Umbenennen ist Speichern unter dem neuen Namen plus Löschen des alten. Die Auswahllisten (Haupt- und Substats) stehen in `data/BuildEditing.kt` und müssen mit `web/index.html` und `desktop/widgets.py` übereinstimmen.

## Bauen und Testen

```sh
cd android
echo "sdk.dir=$HOME/Android/Sdk" > local.properties   # einmalig, nicht eingecheckt
./gradlew :app:testDebugUnitTest      # Tests gegen shared/testdata und shared/stammdaten.json
./gradlew :app:assembleDebug          # app/build/outputs/apk/debug/app-debug.apk
```

Oder den Ordner `android/` in Android Studio öffnen.

Im Debug-Build ist Klartext-HTTP zu `10.0.2.2` und `localhost` erlaubt, um im Emulator gegen einen lokalen PHP-Server (`php -S 127.0.0.1:8000`) zu testen; als Server-Adresse dann `http://10.0.2.2:8000`. Release-Builds erlauben nur HTTPS.

## Nächste Schritte

- Release-Build mit Signierung und Minify
- Offline-Cache der Teams und Builds
- Registrierung neuer Konten in der App
