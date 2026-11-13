# Genshin Impact – Team & Build Manager

Web-App zum Zusammenstellen von Genshin-Impact-Teams und Verwalten der Charakter-Builds. Jeder Nutzer hat ein eigenes Konto und eigene Teams.

## Funktionen

- Registrierung und Login (Session-basiert)
- Teams mit bis zu 4 Charakteren anlegen, speichern und löschen; die Karten lassen sich per Drag & Drop am Kopfbereich oder mit den Pfeilen ‹ › umsortieren
- Pro Charakter: Level, Konstellation, Talente, Waffe (Level, Raffinierung), Artefaktsets (4er oder 2×2er, mit Tooltip der Set-Boni) und Waffe (Tooltip mit dem Passiv zur gewählten Veredelung) und die Substats aller 5 Artefakte (Blume, Feder, Sanduhr, Kelch, Krone), je mit dem Namen des Teils (Dropdown mit Suchfeld: Teile der gewählten Sets zuerst, danach alle übrigen für ein Off-Piece)
- Suchbare Auswahllisten für Charaktere und Waffen
- Kopfzeile mit Benutzermenü (Exportieren, Importieren, Logout); die Team-Steuerung darunter bricht auf schmalen Displays gruppenweise um und lässt sich am Handy bedienen

Builds werden **pro Nutzer und Charakter** gespeichert, nicht pro Team. Ändert man den Build eines Charakters, gilt die Änderung in allen Teams, in denen er vorkommt.

## Technik

- **Frontend:** eine einzelne `index.html` mit Vanilla JavaScript und Tailwind CSS (CDN)
- **Backend:** PHP-Endpunkte in `api/` (PDO), JSON-API
- **Datenbank:** MySQL / MariaDB

Es gibt keinen Build-Schritt und keine Abhängigkeiten, die installiert werden müssen.

```
index.html          Komplettes Frontend
tests/              Tests des Frontends (Node, jsdom), nicht für den Server
api/
  db.php            Datenbankverbindung
  auth_check.php    Session-Setup, Bearer-Token, require_login()
  auth.php          ?action=status|register|login|token|logout|delete_account
  rate_limit.php    Begrenzung von Anmelde- und Registrierungsversuchen
  characters.php    Charakterliste (GET)
  weapons.php       Waffenliste (GET)
  artifacts.php     Artefaktsets (GET)
  teams.php         Teams des Nutzers (GET / POST / DELETE)
assets/             Symlink auf ../shared/assets (Bilder <name>.png, Schriftart zh-cn.ttf)
```

## Einrichtung

1. **Webserver mit PHP** (z. B. Apache oder nginx + PHP-FPM) mit der PDO-MySQL-Erweiterung. Der Inhalt von `web/` muss im **Web-Root** liegen (beim Hochladen den Symlink `assets` auflösen und `tests/` weglassen, z. B. `rsync -rL --exclude tests web/ …`), weil das Frontend absolute Pfade (`/api`, `/assets/images`) verwendet.

2. **Datenbank** anlegen. `schema.sql` enthält das Schema, ist aber aus den Abfragen in `api/*.php` abgeleitet und nicht aus der Produktivdatenbank exportiert (vorher mit `SHOW CREATE TABLE` abgleichen). Eine bestehende Datenbank braucht nur die Dateien aus `migrations/` (aktuell `001_api_tokens.sql` bis `006_stat_vtd.sql`). Wichtig sind die eindeutigen Schlüssel `teams (user_id, name)` und `user_characters (user_id, char_name)`.

3. **Zugangsdaten** konfigurieren – entweder per Datei:

   ```sh
   cp api/config.example.php api/config.local.php
   # Werte in api/config.local.php eintragen
   ```

   oder per Umgebungsvariablen (haben Vorrang): `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS`, `DB_CHARSET`.

   `api/config.local.php` ist in `.gitignore` eingetragen und wird nicht eingecheckt.

4. Für einen schnellen lokalen Test reicht der eingebaute PHP-Server:

   ```sh
   php -S localhost:8000
   ```

   Danach http://localhost:8000 öffnen.

## Tests

```sh
cd web/tests
npm install
npm test
```

`tests/frontend.test.js` lädt `index.html` in jsdom (mit einer fetch-Attrappe, Stammdaten aus `shared/stammdaten.json`) und prüft das Verschieben der Teamkarten (Pfeile, Drag & Drop, Ablage auf dem freien Platz, ignorierte fremde Drags, gesendete Reihenfolge), das Benutzermenü und die Anzeige von Anmeldefehlern. jsdom kennt kein echtes Drag & Drop, die Ereignisse werden nachgebaut; das Verhalten beim Ziehen mit der Maus im Browser prüft das nicht. Benötigt wird Node.js 20 oder neuer; `tests/` gehört nicht zum Deployment.

## Begrenzung von Anmeldungen und Registrierungen

Schutz vor Durchprobieren von Passwörtern und vor massenhaftem Anlegen von Konten (`api/rate_limit.php`, Tabelle `auth_attempts` aus `migrations/002_auth_attempts.sql`). Bei Überschreitung antwortet die API mit **HTTP 429**, dem Header `Retry-After` und einer deutschen Meldung („Zu viele Anmeldeversuche. Bitte versuche es in 12 Minuten erneut.“), die Web-Oberfläche und die Android-App anzeigen.

| Aktion | Gezählt | Grenze | Fenster |
|---|---|---|---|
| Anmeldung (Session und Token) | Fehlversuche je Benutzername | 8 | 15 Minuten |
| Anmeldung (Session und Token) | Fehlversuche je IP-Adresse | 15 | 15 Minuten |
| Registrierung | Versuche je IP-Adresse | 5 | 1 Stunde |
| Registrierung | Versuche insgesamt | 60 | 1 Stunde |

- Gesperrt wird auch bei **richtigem** Passwort, bis die Sperre abläuft; eine erfolgreiche Anmeldung setzt den Zähler des Benutzernamens zurück. Ein unbekannter Benutzername wird genauso gezählt (kein Erraten von Konten über das Sperrverhalten).
- Die Werte stehen als Konstanten am Anfang von `rate_limit.php`.
- Gespeichert werden nur SHA-256-Werte von IP und Benutzername, nie Klartext; Zeilen werden nach spätestens 2 Stunden gelöscht.
- **Client-IP:** Hinter einem Reverse-Proxy (nginx) steht in `REMOTE_ADDR` die Adresse des Proxys. Deshalb gilt `X-Real-IP` bzw. das erste `X-Forwarded-For`, aber nur, wenn die Verbindung von einer lokalen oder privaten Adresse kommt (sonst ließe sich der Header fälschen). Ist der Client nicht bestimmbar, gibt es keine IP-Begrenzung, nur die je Benutzername.
- **Ausfallsicher:** Fehlt die Tabelle (Migration noch nicht gelaufen) oder schlägt die Zählung fehl, wird nicht gesperrt und die Anmeldung funktioniert wie zuvor. Code und Migration können in beliebiger Reihenfolge eingespielt werden.
- **Grenze des Verfahrens:** Wer den Namen eines Kontos kennt, kann es durch absichtliche Fehlversuche für 15 Minuten sperren. Das ist der Preis der Sperre je Benutzername.

Tests: `web/tests/rate_limit_test.php` (Logik direkt gegen die Datenbank, nur lokal) und `web/tests/api_rate_limit.sh <Adresse>` (Ende-zu-Ende über HTTP, nur lokal). Beide laufen gegen die Datenbank aus „Lokal gegen echtes MariaDB testen“, auch gegen MySQL 5.7.

## Token-Login für Apps

Clients ohne Cookies (z. B. die Android-App) melden sich über `POST api/auth.php?action=token` mit `{username, password, device?}` an und erhalten `{token, expires_at, username}`. Danach senden sie bei jeder Anfrage den Token mit, entweder als `Authorization: Bearer <token>` oder als `X-Auth-Token: <token>`; alle Endpunkte mit `require_login()` akzeptieren das wie eine Session. Ein Token gilt 90 Tage, pro Nutzer bleiben höchstens 10 gültig, in der Datenbank steht nur der SHA-256-Hash. `POST api/auth.php?action=logout` mit Token widerruft ihn. **Nur über HTTPS betreiben.**

**Konto löschen:** `POST api/auth.php?action=delete_account` mit `{password}` (Session oder Token) löscht den Nutzer samt Teams, Teammitgliedern, Builds und allen Token in einer Transaktion und beendet die Session. Das Passwort muss erneut stimmen; ein falsches ergibt 403 (bewusst nicht 401, das die Apps als „Sitzung abgelaufen“ deuten) und zählt für die Begrenzung wie ein fehlgeschlagener Login. Es ist keine Migration nötig. Test: `web/tests/api_delete_account.sh <Adresse>` (nur lokal, gegen die Datenbank aus „Lokal gegen echtes MariaDB testen“; der Container muss `gtm-mariadb` heißen).

**Warum zwei Header?** Viele Hoster reichen den `Authorization`-Header nicht an PHP durch (nginx mit PHP-FPM, Apache mit CGI), eigene Header kommen dagegen immer an. Die Android-App sendet deshalb beide, und `auth_check.php` nimmt den Bearer-Token, wenn er ankommt, sonst `X-Auth-Token`. Eine Serverkonfiguration ist dafür nicht nötig. Ob der Header bei dir ankommt, lässt sich mit einem kleinen PHP-Skript prüfen, das `isset($_SERVER['HTTP_AUTHORIZATION'])` und `isset($_SERVER['HTTP_X_AUTH_TOKEN'])` ausgibt.

## Lokal gegen echtes MariaDB testen

Ohne eigenen MySQL-Server lässt sich die API mit Podman prüfen (Port 3306 muss frei sein; `db.php` kennt keinen anderen):

```sh
podman run -d --name gtm-mariadb -e MARIADB_ROOT_PASSWORD=testroot -e MARIADB_DATABASE=genshin-manager \
  -p 127.0.0.1:3306:3306 docker.io/library/mariadb:lts
podman exec -i gtm-mariadb mariadb -uroot -ptestroot genshin-manager < web/schema.sql
# Stammdaten aus ../shared/stammdaten.json in characters/weapons/artifacts einspielen, dann:
cd web && DB_HOST=127.0.0.1 DB_NAME=genshin-manager DB_USER=root DB_PASS=testroot \
  php -d extension=pdo_mysql -S 127.0.0.1:8000
```

Der Emulator erreicht den Rechner unter `http://10.0.2.2:8000`. Aufräumen: `podman rm -f gtm-mariadb`. Auf Arch Linux ist `pdo_mysql` installiert, aber in der `php.ini` deaktiviert, daher der Parameter `-d extension=pdo_mysql`.

## Bilder

Bilder werden anhand des Namens gefunden: Kleinbuchstaben, Leerzeichen werden zu `_`, Apostrophe und Bindestriche fallen weg, alles ab `(` wird ignoriert. Beispiel: „Hu Tao“ → `assets/images/hu_tao.png`.

## Hinweis

Inoffizielles Fanprojekt, nicht mit HoYoverse verbunden. Genshin Impact sowie zugehörige Namen und Bilder sind Eigentum von HoYoverse.
