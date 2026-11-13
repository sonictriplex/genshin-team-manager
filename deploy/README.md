# Deployment der Web-Version

`deploy.sh` lädt die Web-Version (`web/` plus `shared/assets`) per FTPS auf den Server.

```sh
cp deploy/deploy.example.env deploy/deploy.local.env   # einmalig ausfüllen
deploy/deploy.sh --dry-run    # zeigt nur, was sich ändern würde
deploy/deploy.sh              # lädt Geändertes hoch
```

## Verhalten
- **Nur Geändertes:** Verglichen wird bei Bildern nach Größe, bei `*.php` und `*.html` nach Inhalt.
- **Sicherung:** Dateien, die überschrieben werden, landen vorher in `deploy/backup/<Zeitstempel>/`.
- **Nie gelöscht:** Dateien auf dem Server, die es lokal nicht gibt, bleiben unberührt.
- **Nie hochgeladen:** `api/db.php` und `api/config.local.php` (Datenbank-Zugangsdaten des Servers). Auch `tests/` bleibt lokal.
- **Danach:** Das Skript prüft, ob die Startseite mit HTTP 200 antwortet.
- Das Passwort wird nicht in der Prozessliste sichtbar: Es geht über eine temporäre Datei mit Rechten nur für den Benutzer.

## Zugangsdaten (`deploy.local.env`, nicht im Git)
| Variable | Bedeutung |
|---|---|
| `FTP_HOST` | Servername mit gültigem TLS-Zertifikat. Beim Hoster dogado nicht die eigene Domain, sondern `webNNN.dogado.net` (die Domain hat kein passendes Zertifikat) |
| `FTP_USER`, `FTP_PASS` | FTP-Zugang |
| `FTP_DIR` | Web-Root relativ zur FTP-Wurzel, ohne Schrägstriche am Rand |
| `SITE_URL` | optional, wird nach dem Upload geprüft |

Die Dateien `deploy.local.env` und `backup/` stehen in `.gitignore`. In `backup/` liegt u. a. die ältere `db.php` des Servers mit Zugangsdaten, sie gehört nie ins Git.

## Datenbank-Änderungen (Migrationen)
Neue Tabellen stehen in `web/migrations/` und müssen einmal auf dem Server ausgeführt werden (z. B. in phpMyAdmin, oder per Einmal-Skript über den Webserver, das die `db.php` des Servers benutzt und sich danach selbst löscht). Der Code ist so geschrieben, dass er auch ohne die neue Tabelle weiterläuft; die Reihenfolge von Upload und Migration ist daher egal.

Eine Migration ist erledigt, wenn die Tabelle existiert. Stand Produktivserver: `001_api_tokens` und `002_auth_attempts` sind ausgeführt; `003_team_position` (Reihenfolge der Teams) muss **vor** dem Hochladen des neuen Codes ausgeführt werden, weil `teams.php` und `transfer.php` die Spalte `position` voraussetzen. `004_artifact_pieces` (Namen der Artefaktteile, Spalte `artifacts.pieces_json` samt Daten) kann vor oder nach dem Hochladen laufen: Ohne sie liefert `artifacts.php` die Sets ohne Teilnamen, die Dropdowns bleiben dann leer. `005_weapon_passives` (Passiv-Beschreibungen der Waffen für die Tooltips, Datei ca. 390 KB, bei einem kleinen phpMyAdmin-Importlimit in Teilen einspielen) ist ebenfalls unabhängig von der Reihenfolge; ohne sie fehlen nur die Waffen-Tooltips.

## Wiederherstellen (alten Stand zurückspielen)
Die gesicherte Datei aus `backup/<Zeitstempel>/` wieder hochladen, oder den alten Stand aus dem Git holen (`git checkout <Commit> -- web/index.html`) und `deploy.sh` ausführen.
