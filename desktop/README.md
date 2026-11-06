# Genshin Team-Slots Manager

Desktop-App zum Zusammenstellen von Genshin-Impact-Teams und zum Verwalten der Charakter-Builds. Gebaut mit Python, PySide6 (Qt) und SQLite.

## Funktionen

- **Teams**: Teams mit bis zu 4 Charakteren anlegen, speichern, laden, umbenennen und löschen
- **Charakter-Builds**: pro Charakter Level, Sternbild (C0–C6), Waffe mit Level und Veredelung, zwei Artefaktsets und Talentstufen (A/E/Q)
- **Artefakt-Detailwerte**: für Blume, Feder, Sanduhr, Kelch und Krone jeweils Seltenheit, Level, Hauptwert und bis zu 4 Substats
- **Suche**: Charaktere nach Region, Element und Seltenheit filtern, Waffen nach Typ und Seltenheit
- **Tooltips** mit den 2er- und 4er-Boni der Artefaktsets

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

Die App lässt sich aus jedem Verzeichnis starten; Datenbank und Bilder werden relativ zum Projektordner gefunden.

## Datenbank

Alle Daten liegen in `genshin_manager.db` im Projektordner. Die Datei ist **nicht im Git-Repository**, weil sie neben den Stammdaten auch persönliche Teams und Builds enthält. Sie sollte daher separat gesichert werden.

Fehlende Tabellen legt die App beim Start automatisch an. Eine neue, leere Datenbank enthält aber keine Charaktere, Waffen oder Artefaktsets.

### Tabellen

| Tabelle | Inhalt |
|---|---|
| `characters` | Stammdaten: Name, Element, Waffentyp, Region, Seltenheit, Icon-Pfad |
| `weapons` | Stammdaten: Name, Waffentyp, Seltenheit |
| `artifacts` | Stammdaten: Artefaktsets mit 1er-, 2er- und 4er-Bonus |
| `user_characters` | Builds je Charakter; die Artefakt-Detailwerte liegen als JSON in `artifact_stats_json` |
| `teams` | Teamnamen |
| `team_members` | Zuordnung Team → Charakter mit Slot-Reihenfolge |

## Projektstruktur

```
main.py            Startpunkt, setzt das Stylesheet und öffnet das Hauptfenster
main_window.py     Hauptfenster: Teamübersicht, Detailansicht, Speichern/Laden von Teams
widgets.py         Charakterkarte, leerer Slot, Artefakt-Detailpanel
dialogs.py         Such- und Auswahldialoge für Charaktere und Waffen
styles.py          Zentrales Qt-Stylesheet und Farbpalette
manager.py         GenshinManager: Datenbankzugriff, Schema
models.py          Datenklassen (Character, Weapon, ArtifactSet) und Pfad-Hilfsfunktionen
assets/images/     Icons der Charaktere und Waffen
```

## Icons

Icons werden in `assets/images/` über den Namen gefunden: Kleinbuchstaben, Leerzeichen und Bindestriche werden zu `_`, Klammerzusätze fallen weg. Beispiele:

- `Kaedehara Kazuha` → `kaedehara_kazuha.png`
- `Traveler (Dendro)` → `traveler.png`, sofern in der Datenbank kein eigener Pfad hinterlegt ist

Fehlt ein Icon, zeigt die Karte stattdessen den Namen an. Für einige Waffen gibt es noch keine Bilder.
