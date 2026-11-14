# Genshin Team-Slots Manager

Desktop-App zum Zusammenstellen von Genshin-Impact-Teams und zum Verwalten der Charakter-Builds. Gebaut mit Python, PySide6 (Qt) und SQLite.

## Funktionen

- **Teams**: Teams mit bis zu 4 Charakteren anlegen, speichern, laden, umbenennen und löschen; die Reihenfolge der Karten ändert man per Drag & Drop am Kopfbereich der Karte oder mit den Pfeilen ‹ ›
- **Charakter-Builds**: pro Charakter Level, Sternbild (C0–C6), Waffe mit Level und Veredelung, zwei Artefaktsets und Talentstufen (A/E/Q)
- **Artefakt-Detailwerte**: für Blume, Feder, Sanduhr, Kelch und Krone jeweils der Name des Teils (Suchfeld mit Vorschlägen: Teile der gewählten Sets fett oben, dazu alle anderen für ein Off-Piece), Seltenheit, Level, Hauptwert und bis zu 4 Substats
- **Werkzeugleiste**: Name, Speichern und Neues Team links, Teamauswahl und Löschen (Symbolknopf mit Rückfrage) rechts; Exportieren und Importieren im Menü „Datei“
- **Suche**: Charaktere nach Region, Element und Seltenheit filtern, Waffen nach Typ und Seltenheit
- **Tooltips** mit den Boni der Artefaktsets (an der Auswahl und in der Liste) und dem Passiv der Waffe (passend zur Veredelung, auch in der Waffensuche)

Ein Build gilt für den Charakter, nicht für das Team: Wird ein Charakter in mehreren Teams verwendet, hat er überall denselben Build.

## Voraussetzungen

- Python 3.10 oder neuer (entwickelt mit 3.14)
- PySide6 6.12 oder neuer

## Installation und Start

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python main.py
```

Die App lässt sich aus jedem Verzeichnis starten; Datenbank (`desktop/genshin_manager.db`) und Bilder (`shared/`) werden relativ zum Repo gefunden.

## Datenbank

Alle Daten liegen in `genshin_manager.db` im Projektordner. Die Datei ist **nicht im Git-Repository**, weil sie neben den Stammdaten auch persönliche Teams und Builds enthält. Sie sollte daher separat gesichert werden.

### Stammdaten

Die Stammdaten (Charaktere, Waffen, Artefaktsets) liegen versioniert in `shared/stammdaten.json`. Beim Start legt die App fehlende Tabellen an und spielt die Stammdaten ein, wenn die Datenbank noch keine hat. Eine frische Kopie des Repos läuft also ohne weitere Schritte. Teams und Builds sind nicht darin enthalten, sie bleiben privat in der Datenbank.

Von Hand lassen sich die Stammdaten so verwalten:

```bash
python seed.py import    # fehlende Einträge in die Datenbank einspielen (vorhandene bleiben unverändert)
python seed.py export    # Stammdaten aus der Datenbank in shared/stammdaten.json schreiben
```

Neue Charaktere oder Waffen trägt man also in die Datenbank ein und führt danach `python seed.py export` aus, damit sie auch im Repo landen. Alternativ ergänzt man sie direkt in der JSON-Datei und führt `python seed.py import` aus.

### Tabellen

| Tabelle | Inhalt |
|---|---|
| `characters` | Stammdaten: Name, Element, Waffentyp, Region, Seltenheit, Icon-Pfad |
| `weapons` | Stammdaten: Name, Waffentyp, Seltenheit |
| `artifacts` | Stammdaten: Artefaktsets mit 1er-, 2er- und 4er-Bonus |
| `user_characters` | Builds je Charakter; die Artefakt-Detailwerte liegen als JSON in `artifact_stats_json` |
| `teams` | Teamnamen |
| `team_members` | Zuordnung Team → Charakter mit Slot-Reihenfolge |

## Tests

```bash
cd desktop
python -m unittest discover -s tests -v
```

`tests/test_card_order.py` prüft das Verschieben der Karten (Pfeile, Drag & Drop, Speichern der Reihenfolge) und die Migration älterer Datenbanken auf `weapons.icon_path`. Die Oberfläche läuft ohne Bildschirm (`QT_QPA_PLATFORM=offscreen`), die Datenbank ist eine Wegwerf-Datei; zusätzliche Pakete sind nicht nötig. Das Ziehen mit der Maus selbst lässt sich so nicht auslösen: Getestet wird, dass ein Drag am Kartenkopf startet und das Ablegen die richtige Position trifft.

## Projektstruktur

```
icons/             Symbole der Oberfläche (SVG)
main.py            Startpunkt, setzt das Stylesheet und öffnet das Hauptfenster
main_window.py     Hauptfenster: Teamübersicht, Detailansicht, Speichern/Laden von Teams
widgets.py         Charakterkarte, leerer Slot, Artefakt-Detailpanel
dialogs.py         Such- und Auswahldialoge für Charaktere und Waffen
styles.py          Zentrales Qt-Stylesheet und Farbpalette
manager.py         GenshinManager: Datenbankzugriff, Schema, Einspielen der Stammdaten
seed.py            Import/Export der Stammdaten (python seed.py import|export)
tests/             Tests (unittest)
models.py          Datenklassen (Character, Weapon, ArtifactSet) und Pfad-Hilfsfunktionen
../shared/          gemeinsam genutzt: stammdaten.json (Charaktere, Waffen, Artefaktsets) und assets/images/ (Bilder in den Unterordnern characters, weapons, artifacts, ui)
```

## Icons

Icons werden in `shared/assets/images/characters/` (Charaktere) bzw. `weapons/` (Waffen) über den Namen gefunden: Kleinbuchstaben, Leerzeichen und Bindestriche werden zu `_`, Klammerzusätze fallen weg. Beispiele:

- `Kaedehara Kazuha` → `characters/kaedehara_kazuha.png`
- `Traveler (Dendro)` → `characters/traveler.png`, sofern in der Datenbank kein eigener Pfad hinterlegt ist

Fehlt ein Icon, zeigt die Karte stattdessen den Namen an. Für einige Waffen gibt es noch keine Bilder.
