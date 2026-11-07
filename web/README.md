# Genshin Impact – Team & Build Manager

Web-App zum Zusammenstellen von Genshin-Impact-Teams und Verwalten der Charakter-Builds. Jeder Nutzer hat ein eigenes Konto und eigene Teams.

## Funktionen

- Registrierung und Login (Session-basiert)
- Teams mit bis zu 4 Charakteren anlegen, speichern und löschen
- Pro Charakter: Level, Konstellation, Talente, Waffe (Level, Raffinierung), Artefaktsets (4er oder 2×2er) und die Substats aller 5 Artefakte (Blume, Feder, Sanduhr, Kelch, Krone)
- Suchbare Auswahllisten für Charaktere und Waffen

Builds werden **pro Nutzer und Charakter** gespeichert, nicht pro Team. Ändert man den Build eines Charakters, gilt die Änderung in allen Teams, in denen er vorkommt.

## Technik

- **Frontend:** eine einzelne `index.html` mit Vanilla JavaScript und Tailwind CSS (CDN)
- **Backend:** PHP-Endpunkte in `api/` (PDO), JSON-API
- **Datenbank:** MySQL / MariaDB

Es gibt keinen Build-Schritt und keine Abhängigkeiten, die installiert werden müssen.

```
index.html          Komplettes Frontend
api/
  db.php            Datenbankverbindung
  auth_check.php    Session-Setup, Bearer-Token, require_login()
  auth.php          ?action=status|register|login|token|logout
  characters.php    Charakterliste (GET)
  weapons.php       Waffenliste (GET)
  artifacts.php     Artefaktsets (GET)
  teams.php         Teams des Nutzers (GET / POST / DELETE)
assets/             Symlink auf ../shared/assets (Bilder <name>.png, Schriftart zh-cn.ttf)
```

## Einrichtung

1. **Webserver mit PHP** (z. B. Apache oder nginx + PHP-FPM) mit der PDO-MySQL-Erweiterung. Der Inhalt von `web/` muss im **Web-Root** liegen (beim Hochladen den Symlink `assets` auflösen, z. B. `rsync -rL web/ …`), weil das Frontend absolute Pfade (`/api`, `/assets/images`) verwendet.

2. **Datenbank** anlegen. `schema.sql` enthält das Schema, ist aber aus den Abfragen in `api/*.php` abgeleitet und nicht aus der Produktivdatenbank exportiert (vorher mit `SHOW CREATE TABLE` abgleichen). Eine bestehende Datenbank braucht nur die Dateien aus `migrations/` (aktuell `001_api_tokens.sql`). Wichtig sind die eindeutigen Schlüssel `teams (user_id, name)` und `user_characters (user_id, char_name)`.

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

## Token-Login für Apps

Clients ohne Cookies (z. B. die Android-App) melden sich über `POST api/auth.php?action=token` mit `{username, password, device?}` an und erhalten `{token, expires_at, username}`. Danach senden sie bei jeder Anfrage `Authorization: Bearer <token>`; alle Endpunkte mit `require_login()` akzeptieren das wie eine Session. Ein Token gilt 90 Tage, pro Nutzer bleiben höchstens 10 gültig, in der Datenbank steht nur der SHA-256-Hash. `POST api/auth.php?action=logout` mit Token widerruft ihn. **Nur über HTTPS betreiben.**

Voraussetzung: der Webserver muss den `Authorization`-Header an PHP durchreichen. Bei Apache mit CGI/FPM fehlt er oft; dort hilft in der `.htaccess` die Zeile `SetEnvIf Authorization "(.+)" HTTP_AUTHORIZATION=$1`. Bei nginx + PHP-FPM wird er normalerweise durchgereicht.

## Bilder

Bilder werden anhand des Namens gefunden: Kleinbuchstaben, Leerzeichen werden zu `_`, Apostrophe und Bindestriche fallen weg, alles ab `(` wird ignoriert. Beispiel: „Hu Tao“ → `assets/images/hu_tao.png`.

## Hinweis

Inoffizielles Fanprojekt, nicht mit HoYoverse verbunden. Genshin Impact sowie zugehörige Namen und Bilder sind Eigentum von HoYoverse.
