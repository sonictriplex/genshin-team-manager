# Änderungsverlauf

Die Android-App wird nicht als fertige APK verteilt, sondern bei Bedarf selbst gebaut (siehe [android/README.md](android/README.md)); die Web-Version läuft per `deploy/deploy.sh` auf dem Server, der Desktop direkt aus dem Repo. Dieser Verlauf fasst die wichtigsten Änderungen zusammen. Seit 1.6.0 haben Web, Android und Desktop dieselbe Versionsnummer (der „Über“-Dialog war bereits in den ersten 1.6.0-Ständen enthalten und ist hier unter 1.6.1 beschrieben); frühere Web-Versionen (1.0.0–1.4.0) sind rückwirkend aus dem Git-Verlauf vergeben.

## Desktop 1.6.1 (11.11.2026)
- Neuer „Über“-Dialog (Menü Hilfe → Über…): Paimon-Bild, Name, Version, Kurzbeschreibung, Hinweis „Inoffizielles Fanprojekt, nicht mit HoYoverse verbunden“ und das media-matrix-Logo
- Die Versionsnummer steht jetzt im Code (`APP_VERSION` in `desktop/models.py`); ein Test gleicht sie mit diesem Changelog ab

## Web 1.6.1 (11.11.2026)
- Neuer „Über“-Dialog (Benutzermenü → Über): Paimon-Bild, Name, Version, Kurzbeschreibung, Fanprojekt-Hinweis und das media-matrix-Logo; schließt per Schließen-Knopf, Escape oder Klick daneben
- Ein Test gleicht die angezeigte Version mit diesem Changelog ab

## Android 1.6.1 (11.11.2026)
- Neuer „Über“-Dialog (Menü ⋮ → Über): Paimon-Bild, Name, Version, Kurzbeschreibung, Fanprojekt-Hinweis und das media-matrix-Logo; die Version kommt automatisch aus der App

## Desktop 1.6.0 (11.11.2026)
- Web, Android und Desktop tragen jetzt gemeinsam die Version 1.6.0. Ein Konto zum Löschen gibt es am Desktop nicht (lokale Daten)

## Web 1.6.0 (11.11.2026)
- Konto löschen: Benutzermenü → „Konto löschen“, nach Passwortabfrage werden Konto, Teams und Builds endgültig gelöscht (auch in der Android-App). Neuer Endpunkt `auth.php?action=delete_account`, keine Migration nötig, Test `web/tests/api_delete_account.sh`

## Android 1.6.0 (11.11.2026)
- Konto löschen: Menü ⋮ → „Konto löschen“, nach Passwortabfrage werden Konto, Teams und Builds endgültig gelöscht (auch in der Web-Version)

## Android 1.5.0 (11.11.2026)
- Tablet-Layout: Teams in zwei (Hochformat) bzw. drei Spalten (Querformat), Build-Ansicht und -Bearbeitung zweispaltig; Inhalt ist zentriert und in der Breite begrenzt
- Handys bleiben im Hochformat gesperrt; Tablets lassen sich frei drehen, ohne dass ungespeicherte Änderungen beim Drehen verloren gehen

## Android 1.4.2 (10.11.2026)
- Knopf „Neues Team“ unten rechts zeigt nur noch ein „+“

## Desktop 1.1.4 (10.11.2026)
- Rahmen der Teamkarten (auch beim Darüberfahren mit der Maus) wird wieder angezeigt

## Desktop 1.1.3 (10.11.2026)
- Hintergrundbild leicht verwaschen, hinter den Teamkarten als Milchglas (wie in der Web-Version)

## Desktop 1.1.2 (10.11.2026)
- Fenster startet mit 1080×670 und lässt sich nicht kleiner ziehen

## Desktop 1.1.1 (10.11.2026)
- Verschieben-Pfeile auf den Teamkarten sind wieder sichtbar (neue runde Knöpfe)

## Desktop 1.1.0 (10.11.2026)
- Hintergrundbild wie in der Web- und Android-Version (mit dunkler Abdeckung)

## Web 1.4.0 (10.11.2026)
- Übersicht aller Teams: Charakterlevel klein oben links im Bild, Bilder mit transparentem Hintergrund in der Elementfarbe, durchsichtigere Teamkarten (auch Desktop und Android)
- Charakternamen auf den Charakterkarten in der Genshin-Schrift; zu lange Namen werden verkleinert, bis sie ganz lesbar sind (auch Desktop)

## Android 1.4.1 (10.11.2026)
- Teamliste: Charakterlevel klein oben links im Bild, Bilder mit transparentem Hintergrund in der Elementfarbe, durchsichtigere Teamkarten
- Zu lange Titel (z. B. Charakternamen) werden verkleinert, bis sie ganz lesbar sind

## Android 1.4.0 (09.11.2026)
- Teams in der Liste per Pfeil nach oben/unten verschieben; die Reihenfolge wird auf dem Server gespeichert

## Web 1.3.0 (09.11.2026)
- Teams in der Übersicht verschieben (Pfeile und Drag & Drop); die Reihenfolge wird gespeichert (neue Spalte `teams.position`, Migration `003_team_position.sql`, `teams.php` nimmt `{order: [...]}` an; auch Desktop und Android)
- Ein Charakter, der schon in einem anderen Team ist, behält beim Hinzufügen zu einem neuen Team seinen Build (vorher startete er mit Standardwerten und überschrieb den gespeicherten Build)

## Android 1.3.0 (08.11.2026)
- App-Icon zeigt Lan Yan
- Hintergrundbild wie in der Web-Version

## Web 1.2.0 (08.11.2026)
- Übersicht aller Teams (zwei pro Zeile, Icons füllen die Kartenbreite); die Seite startet damit, „Alle Teams“ und „Neues Team“ stehen im Menü (auch Desktop)
- Teams lassen sich umbenennen
- Logo the media-matrix zentriert im Footer

## Android 1.2.1 (07.11.2026)
- Überschrift der Teamliste: „Team & Build Manager“

## Web 1.1.0 (07.11.2026)
- Token-Login für Apps (`auth.php?action=token`, Migration `001_api_tokens.sql`); der Token wird auch als `X-Auth-Token` akzeptiert
- Begrenzung von Anmelde- und Registrierungsversuchen (HTTP 429, `Retry-After`), Migration `002_auth_attempts.sql`
- Kopfzeile wie in der Android-App: Benutzermenü, kompakte Team-Steuerung, Löschen als Symbolknopf (auch Desktop)
- Teamkarten per Drag & Drop und Pfeilen verschieben (auch Desktop)
- Fehlermeldungen der API verraten keine Interna mehr

## Android 1.2.0
- **Konto erstellen** direkt in der App (Registrierung mit Passwortwiederholung, Eingaben werden vorab geprüft)
- Leere Teamliste verweist auf „Neues Team“

## Android 1.1.1
- Aufgeräumte Kopfzeile: Titel einzeilig, „Neu laden“ als Symbol, „Abmelden“ im Menü, „Neues Team“ als Knopf unten rechts
- Teamkarten mit Symbolen für Bearbeiten und Löschen; nichts bricht mehr mitten im Wort um

## Android 1.1.0
- **Offline-Cache** für Teams und Builds (Anzeige ohne Verbindung, Bearbeiten dann gesperrt)
- **Feste Server-Adresse** (kein Serverfeld mehr im Release)

## Android 1.0.1
- Token zusätzlich im Header `X-Auth-Token` (der Hoster reicht `Authorization` nicht an PHP durch)

## Android 1.0.0
- Erste Version: Anmeldung per Token, Teams und Builds ansehen, bearbeiten und speichern, Charaktere umsortieren, Genshin-Design

## Web 1.0.0 (06.11.2026)
- Erste Version in diesem Repository: Anmeldung und Registrierung, Teams und Builds pro Charakter, Detailbereich für Artefakte, Import und Export als JSON (kompatibel mit dem Desktop)

## Projekt
- Desktop, Web und Android in einem Repository, gemeinsame Daten in `shared/` (Stammdaten, Bilder, Austauschformat mit Schema)
- Tests für alle drei Clients (Android 24, Web 24 plus API-Tests, Desktop 20)
- Deploy-Skript `deploy/deploy.sh` (FTPS, nur Geändertes, mit Sicherung)
