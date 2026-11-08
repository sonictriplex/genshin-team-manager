# Änderungsverlauf

Die Android-App wird nicht als fertige APK verteilt, sondern bei Bedarf selbst gebaut (siehe [android/README.md](android/README.md)); die Web-Version läuft per `deploy/deploy.sh` auf dem Server, der Desktop direkt aus dem Repo. Dieser Verlauf fasst die wichtigsten Änderungen zusammen.

## Android 1.2.2 (08.11.2026)
- App-Icon zeigt Lan Yan

## Android 1.2.1 (07.11.2026)
- Überschrift der Teamliste: „Team & Build Manager“

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

## Server / Web
- **Begrenzung von Anmelde- und Registrierungsversuchen** (HTTP 429, `Retry-After`), Migration `002_auth_attempts.sql`
- **Web und Desktop:** Kopfzeile wie in der Android-App (Benutzermenü, kompakte Team-Steuerung, Löschen als Symbolknopf; Desktop fragt vor dem Löschen nach)
- **Web und Desktop:** Teamkarten per Drag & Drop und Pfeilen verschieben
- **Token-Login** für Apps (`auth.php?action=token`), Migration `001_api_tokens.sql`
- Fehlermeldungen der API verraten keine Interna mehr

## Projekt
- Desktop, Web und Android in einem Repository, gemeinsame Daten in `shared/` (Stammdaten, Bilder, Austauschformat mit Schema)
- Tests für alle drei Clients (Android 23, Web 14 plus API-Tests, Desktop 14)
- Deploy-Skript `deploy/deploy.sh` (FTPS, nur Geändertes, mit Sicherung)
