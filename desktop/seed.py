"""Stammdaten (Charaktere, Waffen, Artefaktsets) aus/in `shared/stammdaten.json`.

Die Datenbank selbst liegt nicht im Repository. Damit eine neue, leere Datenbank trotzdem
nutzbar ist, werden die Stammdaten aus der versionierten JSON-Datei eingespielt, und zwar
automatisch beim ersten Start (siehe GenshinManager) oder von Hand:

    python seed.py import      # fehlende Einträge in die Datenbank einspielen
    python seed.py export      # Stammdaten aus der Datenbank in die JSON-Datei schreiben

Teams und Builds gehören nicht dazu und bleiben privat in der Datenbank.
"""
import argparse
import json
import os
import sqlite3

from models import BASE_DIR, SHARED_DIR

DB_PATH = os.path.join(BASE_DIR, "genshin_manager.db")
SEED_PATH = os.path.join(SHARED_DIR, "stammdaten.json")

# Tabelle -> Spalten, die exportiert/importiert werden (die id wird von SQLite vergeben)
TABLES = {
    "characters": ["name", "element", "weapon_type", "region", "rarity", "icon_path"],
    "weapons": ["name", "weapon_type", "rarity", "icon_path"],
    "artifacts": ["name", "bonus_1pc", "bonus_2pc", "bonus_4pc", "pieces_json"],
}


def _row_from_json(table: str, row: dict) -> dict:
    """JSON-Eintrag -> Datenbankzeile (Artefakt-Teilnamen `pieces` werden als Text in `pieces_json` abgelegt)."""
    if table == "artifacts":
        row = dict(row)
        row["pieces_json"] = json.dumps(row.get("pieces") or {}, ensure_ascii=False)
    return row


def _row_to_json(table: str, row: dict) -> dict:
    """Datenbankzeile -> JSON-Eintrag (`pieces_json` wird wieder zum Objekt `pieces`)."""
    if table == "artifacts":
        row = dict(row)
        try:
            row["pieces"] = json.loads(row.pop("pieces_json", None) or "{}")
        except json.JSONDecodeError:
            row["pieces"] = {}
    return row


def export_seed(conn: sqlite3.Connection, path: str = SEED_PATH) -> dict[str, int]:
    """Schreibt die Stammdaten aus der Datenbank in die JSON-Datei. Rückgabe: Anzahl je Tabelle."""
    data = {}
    for table, columns in TABLES.items():
        rows = conn.execute(f"SELECT {', '.join(columns)} FROM {table} ORDER BY id").fetchall()
        data[table] = [_row_to_json(table, dict(zip(columns, row))) for row in rows]

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return {table: len(rows) for table, rows in data.items()}


def import_seed(conn: sqlite3.Connection, path: str = SEED_PATH) -> dict[str, int]:
    """Spielt fehlende Stammdaten ein. Bestehende Einträge (gleicher Name) bleiben unverändert.

    Rückgabe: Anzahl neu eingefügter Einträge je Tabelle.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    inserted = {}
    for table, columns in TABLES.items():
        placeholders = ", ".join("?" for _ in columns)
        sql = f"INSERT OR IGNORE INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        before = conn.total_changes
        rows = [_row_from_json(table, row) for row in data.get(table, [])]
        conn.executemany(sql, [tuple(row.get(c) for c in columns) for row in rows])
        inserted[table] = conn.total_changes - before
    conn.commit()
    return inserted


def fill_artifact_pieces(conn: sqlite3.Connection, path: str = SEED_PATH) -> int:
    """Trägt die Teilnamen der Artefaktsets aus der JSON-Datei nach (für Datenbanken ohne `pieces_json`).

    Rückgabe: Anzahl aktualisierter Sets. Sets ohne Teilnamen in der Datei bleiben unverändert.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    changed = 0
    for row in data.get("artifacts", []):
        pieces = row.get("pieces")
        if not pieces:
            continue
        cur = conn.execute("UPDATE artifacts SET pieces_json = ? WHERE name = ?",
                           (json.dumps(pieces, ensure_ascii=False), row["name"]))
        changed += cur.rowcount
    return changed


def is_seeded(conn: sqlite3.Connection) -> bool:
    """True, wenn alle Stammdaten-Tabellen mindestens einen Eintrag haben."""
    return all(conn.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone() for table in TABLES)


def main():
    parser = argparse.ArgumentParser(description="Stammdaten importieren oder exportieren")
    parser.add_argument("action", choices=["import", "export"])
    parser.add_argument("--db", default=DB_PATH, help="Pfad zur Datenbank (Standard: genshin_manager.db)")
    parser.add_argument("--file", default=SEED_PATH, help="Pfad zur JSON-Datei (Standard: shared/stammdaten.json)")
    args = parser.parse_args()

    if args.action == "import":
        # Schema über den Manager anlegen lassen, falls die Datenbank neu ist
        from manager import GenshinManager
        GenshinManager(args.db, seed_path=None)
        with sqlite3.connect(args.db) as conn:
            counts = import_seed(conn, args.file)
        print("Neu eingespielt:", ", ".join(f"{n} {t}" for t, n in counts.items()))
    else:
        with sqlite3.connect(args.db) as conn:
            counts = export_seed(conn, args.file)
        print(f"Exportiert nach {args.file}:", ", ".join(f"{n} {t}" for t, n in counts.items()))


if __name__ == "__main__":
    main()
