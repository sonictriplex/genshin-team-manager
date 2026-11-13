# Austauschformat (Builds und Teams)

Gemeinsames JSON-Format aller Clients: Desktop (Menü „Datei“), Web (`api/transfer.php`) und Android. Das Schema steht in `exchange-format.schema.json`, eine Referenzdatei in `testdata/export-beispiel.json`.

**Änderungen am Format müssen in allen Clients nachgezogen werden.** Abwärtskompatible Erweiterungen (neue optionale Felder) behalten die `version`. Inkompatible Änderungen erhöhen sie; ältere Clients lehnen dann die Datei ab.

## Aufbau

```json
{
  "format": "genshin-team-manager",
  "version": 1,
  "exported_at": "2026-11-07T00:12:33",
  "builds": [ ... ],
  "teams":  [ ... ]
}
```

| Feld | Bedeutung |
|---|---|
| `format` | Muss `genshin-team-manager` sein |
| `version` | Ganzzahl, aktuell `1`. Ist sie größer als die vom Client unterstützte, wird der Import abgelehnt |
| `exported_at` | Zeitstempel (ISO 8601, ohne Zeitzone) |
| `builds` | Builds je Charakter (ein Build pro Charakter, nicht pro Team) |
| `teams` | Teams mit Charakternamen in Slot-Reihenfolge |

### Build

| Feld | Typ / Bereich | Hinweis |
|---|---|---|
| `name` | String | Charaktername, muss in den Stammdaten existieren |
| `level` | 1–90 | Standard 90 |
| `constellation` | 0–6 | Standard 0 |
| `weapon` | String | Waffenname, leer = keine |
| `weapon_level` | 1–90 | Standard 90 |
| `refinement` | 1–5 | Standard 1 |
| `artifact`, `artifact_2` | String | Artefaktset; leer oder Platzhalter (beginnt mit `—`) = keins |
| `talents` | `{attack, skill, burst}` | je 1–13, Standard 1 |
| `artifact_stats` | Objekt | Slotname → Slot; `{}` wenn leer |

**Slot** (Schlüssel: `Blume`, `Feder`, `Sanduhr`, `Kelch`, `Krone`): `piece` (optional, Name des Artefaktteils, z. B. `"Zuflucht des Gladiators"`, leer = nicht gewählt; kann auch aus einem anderen als dem Build-Set stammen), `rarity` (z. B. `"5★"`), `level`, `main_stat`, `main_value` und `substats`, immer genau 4 Einträge `{stat, val}`. Werte sind Strings mit Dezimalkomma (`"15,7"`). Das Altformat `"KT% + 3.9"` für einen Substat wird beim Import in `{stat, val}` umgewandelt. Die Stats heißen `VTD%` und `VTD (Fix)` (Verteidigung); die älteren Namen `DEF%` und `DEF (Fix)` werden beim Lesen umgewandelt.

### Team

`{ "name": "…", "members": ["Charaktername", …] }`: höchstens 4 Mitglieder, ohne Duplikate, Reihenfolge = Slot.

## Import-Regeln (für alle Clients gleich)

- Unbekannte Charaktere werden übersprungen und in `skipped` gemeldet.
- Zahlen werden auf die Bereiche oben begrenzt; ungültige Werte fallen auf den Standard zurück.
- Gleichnamige Builds und Teams werden überschrieben (`merge`); bei `replace` werden vorher alle Builds und Teams des Nutzers gelöscht.
- Der Import läuft in einer Transaktion: bei einem Fehler bleibt alles unverändert.
- Ergebnis: `{builds: n, teams: n, skipped: [Namen]}`.
