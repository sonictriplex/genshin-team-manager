# Genshin Impact – Team & Build Manager

Teams zusammenstellen und Charakter-Builds verwalten – als Desktop-App und als Web-App. Ein Android-Client ist angedacht.

```
desktop/   Desktop-App (Python, PySide6, SQLite)
web/       Web-App (index.html + PHP-API, MySQL)
shared/    Gemeinsame Daten für alle Clients
  assets/images/    Icons der Charaktere und Waffen, Hintergrund
  assets/zh-cn.ttf  Genshin-Schriftart
  stammdaten.json   Charaktere, Waffen, Artefaktsets
android/   (später)
```

Details stehen in `desktop/README.md` und `web/README.md`.

## Austauschformat

Builds und Teams lassen sich als JSON zwischen allen Clients austauschen (Desktop: Menü „Datei“, Web: `api/transfer.php`). Format: `{"format": "genshin-team-manager", "version": 1, "builds": [...], "teams": [...]}`. Änderungen am Format müssen in allen Clients nachgezogen werden.

## Hinweis zu `web/assets`

`web/assets` ist ein Symlink auf `shared/assets`, damit das Frontend weiter `/assets/...` ansprechen kann. Beim Deployment den Link auflösen, z. B. `rsync -rL web/ server:/pfad/zum/webroot/` (Datei `config.local.php` nicht überschreiben).
