# Android-App

Online-Client für die Web-Version. Die App greift **nicht** direkt auf MySQL zu, sondern über die PHP-API in `../web/api/` (Anmeldung per Token, siehe `../web/README.md`).

**Stand:** Gerüst. Anmelden, Teamliste und schreibgeschützte Build-Ansicht funktionieren. Bearbeiten und Speichern von Teams und Builds fehlt noch.

## Technik

- Kotlin, Jetpack Compose (Material 3), Navigation Compose
- OkHttp und kotlinx.serialization für die API; Token und Server-Adresse in app-privaten SharedPreferences
- `minSdk` 26, `compileSdk` 37, Gradle 9.6 (Wrapper), Android Gradle Plugin 9.5

## Gemeinsame Daten

`app/build.gradle.kts` bindet `../shared` als Asset-Ordner ein. Bilder (`assets/images/…`) und `stammdaten.json` liegen in der APK unter denselben Pfaden wie im Repo. Spezifikationen und Testdaten sowie die Schriftart sind ausgeschlossen. Die Daten werden also nicht kopiert; neue Bilder oder Stammdaten wirken nach einem neuen Build.

Teams und Builds kommen über `api/transfer.php` im [Austauschformat](../shared/exchange-format.md).

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

- Builds und Teams bearbeiten und speichern (`api/teams.php`)
- Charakter-/Waffenauswahl mit Suche
- Token im Android Keystore verschlüsseln
