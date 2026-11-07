import json
import os
import sqlite3
from datetime import datetime
from typing import Optional
from models import Character, Weapon, ArtifactSet, BASE_DIR, DEFAULT_TALENTS, icon_path_for
from seed import SEED_PATH, import_seed, is_seeded

DB_PATH = os.path.join(BASE_DIR, "genshin_manager.db")

# Austauschformat für Import/Export zwischen Desktop- und Web-Version
EXCHANGE_FORMAT = "genshin-team-manager"
EXCHANGE_VERSION = 1
MAX_TEAM_SIZE = 4

SCHEMA = """
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    element TEXT NOT NULL,
    weapon_type TEXT NOT NULL,
    region TEXT NOT NULL,
    rarity INTEGER NOT NULL,
    icon_path TEXT
);
CREATE TABLE IF NOT EXISTS weapons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    weapon_type TEXT NOT NULL,
    rarity INTEGER NOT NULL,
    icon_path TEXT
);
CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    bonus_1pc TEXT DEFAULT '',
    bonus_2pc TEXT DEFAULT '',
    bonus_4pc TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS user_characters (
    char_name TEXT PRIMARY KEY,
    level INTEGER DEFAULT 90,
    constellation INTEGER DEFAULT 0,
    weapon TEXT DEFAULT '',
    weapon_level INTEGER DEFAULT 90,
    refinement INTEGER DEFAULT 1,
    artifact TEXT DEFAULT '',
    artifact_2 TEXT DEFAULT '',
    talent_attack INTEGER DEFAULT 1,
    talent_skill INTEGER DEFAULT 1,
    talent_burst INTEGER DEFAULT 1,
    artifact_stats_json TEXT DEFAULT '{}',
    FOREIGN KEY (char_name) REFERENCES characters(name) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS team_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    char_name TEXT NOT NULL,
    slot_order INTEGER NOT NULL,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (char_name) REFERENCES characters(name) ON DELETE CASCADE,
    UNIQUE (team_id, slot_order)
);
"""


class DatabaseError(Exception):
    """Fehler beim Lesen oder Schreiben der Datenbank (mit verständlicher Meldung für die GUI)."""


class GenshinManager:
    """Verwaltet Charaktere, Waffen, Artefakte, gespeicherte Teams und globale Charakter-Builds via SQLite."""

    def __init__(self, db_path: str = DB_PATH, seed_path: Optional[str] = SEED_PATH):
        self.db_path = db_path
        self.seed_path = seed_path  # None = Stammdaten nicht automatisch einspielen
        self.available_characters: list[Character] = []
        self.available_weapons: list[Weapon] = []
        self.available_artifacts: list[ArtifactSet] = []
        self.saved_teams: dict = {}
        # Fehler beim Start werden gesammelt, damit die GUI sie anzeigen kann
        self.load_errors: list[str] = []

        for step in (self.init_schema, self.seed_if_empty, self.load_characters, self.load_weapons,
                     self.load_artifacts, self.load_teams):
            try:
                step()
            except DatabaseError as e:
                self.load_errors.append(str(e))

    def get_connection(self) -> sqlite3.Connection:
        """Erstellt eine SQLite-Verbindung mit aktivierten Foreign Keys."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_schema(self):
        """Legt fehlende Tabellen an, damit auch eine neue/leere Datenbank funktioniert."""
        try:
            with self.get_connection() as conn:
                conn.executescript(SCHEMA)
                self._migrate_weapon_icons(conn)
        except sqlite3.Error as e:
            raise DatabaseError(f"Datenbank konnte nicht initialisiert werden ({self.db_path}): {e}") from e

    @staticmethod
    def _migrate_weapon_icons(conn: sqlite3.Connection):
        """Ältere Datenbanken: Spalte weapons.icon_path ergänzen und aus vorhandenen Bildern befüllen."""
        columns = [r[1] for r in conn.execute("PRAGMA table_info(weapons)")]
        if "icon_path" in columns:
            return
        conn.execute("ALTER TABLE weapons ADD COLUMN icon_path TEXT")
        for (name,) in conn.execute("SELECT name FROM weapons").fetchall():
            path = icon_path_for(name)
            if os.path.exists(path):
                conn.execute("UPDATE weapons SET icon_path = ? WHERE name = ?",
                             (f"assets/images/{os.path.basename(path)}", name))

    def seed_if_empty(self):
        """Spielt die Stammdaten aus der JSON-Datei ein, wenn die Datenbank noch keine hat."""
        if not self.seed_path:
            return
        try:
            with self.get_connection() as conn:
                if is_seeded(conn):
                    return
                if not os.path.exists(self.seed_path):
                    raise DatabaseError(
                        f"Die Datenbank enthält keine Stammdaten und die Datei {self.seed_path} fehlt."
                    )
                import_seed(conn, self.seed_path)
        except (sqlite3.Error, OSError, json.JSONDecodeError) as e:
            raise DatabaseError(f"Stammdaten konnten nicht eingespielt werden ({self.seed_path}): {e}") from e

    # --- STAMMDATEN LADEN ---

    def load_characters(self):
        """Lädt alle Charaktere aus der SQLite-Datenbank."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, element, weapon_type, region, rarity, icon_path 
                    FROM characters ORDER BY name ASC
                """)
                rows = cursor.fetchall()
                self.available_characters = [
                    Character(
                        name=row[0],
                        element=row[1],
                        weapon_type=row[2],
                        region=row[3],
                        rarity=row[4],
                        icon_path=row[5]
                    ) for row in rows
                ]
        except sqlite3.Error as e:
            self.available_characters = []
            raise DatabaseError(f"Fehler beim Laden der Charaktere: {e}") from e

    def load_weapons(self):
        """Lädt alle Waffen aus der SQLite-Datenbank."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, weapon_type, rarity, icon_path
                    FROM weapons ORDER BY name ASC
                """)
                rows = cursor.fetchall()
                self.available_weapons = [
                    Weapon(name=row[0], weapon_type=row[1], rarity=row[2], icon_path=row[3])
                    for row in rows
                ]
        except sqlite3.Error as e:
            self.available_weapons = []
            raise DatabaseError(f"Fehler beim Laden der Waffen: {e}") from e

    def load_artifacts(self):
        """Lädt Artefaktsets aus der SQLite-Datenbank."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, bonus_1pc, bonus_2pc, bonus_4pc 
                    FROM artifacts ORDER BY name ASC
                """)
                rows = cursor.fetchall()
                self.available_artifacts = [
                    ArtifactSet(
                        name=row[0],
                        bonus_1pc=row[1] or "",
                        bonus_2pc=row[2] or "",
                        bonus_4pc=row[3] or ""
                    ) for row in rows
                ]
        except sqlite3.Error as e:
            self.available_artifacts = []
            raise DatabaseError(f"Fehler beim Laden der Artefakte: {e}") from e

    # --- TEAMS VERWALTEN ---

    def load_teams(self):
        """Lädt alle gespeicherten Teams und deren Mitgliederzuordnung aus der Datenbank."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM teams ORDER BY id ASC")
                teams_rows = cursor.fetchall()

                teams_dict = {}
                for team_id, team_name in teams_rows:
                    cursor.execute("""
                        SELECT char_name FROM team_members 
                        WHERE team_id = ? ORDER BY slot_order ASC
                    """, (team_id,))
                    members = [m[0] for m in cursor.fetchall()]
                    teams_dict[team_name] = members

                self.saved_teams = teams_dict
        except sqlite3.Error as e:
            self.saved_teams = {}
            raise DatabaseError(f"Fehler beim Laden der Teams: {e}") from e

    def save_teams(self):
        """Speichert alle Teams aus self.saved_teams in der SQLite-Datenbank."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Bestehende Teams ermitteln und gelöschte entfernen
                cursor.execute("SELECT name FROM teams")
                existing_teams = {row[0] for row in cursor.fetchall()}
                current_teams = set(self.saved_teams.keys())

                teams_to_delete = existing_teams - current_teams
                for t_name in teams_to_delete:
                    cursor.execute("DELETE FROM teams WHERE name = ?", (t_name,))

                # 2. Teams und Mitglieder aktualisieren / einfügen
                for team_name, char_names in self.saved_teams.items():
                    cursor.execute("INSERT OR IGNORE INTO teams (name) VALUES (?)", (team_name,))
                    cursor.execute("SELECT id FROM teams WHERE name = ?", (team_name,))
                    team_id = cursor.fetchone()[0]

                    # Alte Zuordnungen überschreiben
                    cursor.execute("DELETE FROM team_members WHERE team_id = ?", (team_id,))

                    for slot_idx, c_entry in enumerate(char_names):
                        name = c_entry.get("name", c_entry) if isinstance(c_entry, dict) else c_entry
                        if hasattr(name, "name"):
                            name = name.name

                        if name:
                            cursor.execute("""
                                INSERT INTO team_members (team_id, char_name, slot_order)
                                VALUES (?, ?, ?)
                            """, (team_id, name, slot_idx))

                conn.commit()
        except sqlite3.Error as e:
            # Die Transaktion wurde zurückgerollt -> Speicherstand wieder mit der DB abgleichen
            try:
                self.load_teams()
            except DatabaseError:
                pass
            raise DatabaseError(f"Teams konnten nicht gespeichert werden: {e}") from e

    def rename_team(self, old_name: str, new_name: str):
        """Benennt ein Team in der DB um (ID und Reihenfolge bleiben erhalten).

        Ein bereits existierendes Team mit dem neuen Namen wird dabei ersetzt.
        """
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM teams WHERE name = ?", (new_name,))
                conn.execute("UPDATE teams SET name = ? WHERE name = ?", (new_name, old_name))
        except sqlite3.Error as e:
            raise DatabaseError(f"Team '{old_name}' konnte nicht umbenannt werden: {e}") from e

        # Speicherstand anpassen, Position des Teams beibehalten
        self.saved_teams = {
            (new_name if name == old_name else name): members
            for name, members in self.saved_teams.items()
            if name != new_name
        }

    # --- ZENTRALE CHARAKTER-BUILDS VERWALTEN ---

    def load_user_characters(self) -> dict:
        """Lädt alle zentral gespeicherten Charakter-Builds aus der Datenbank."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT char_name, level, constellation, weapon, weapon_level, refinement,
                           artifact, artifact_2, talent_attack, talent_skill, talent_burst, artifact_stats_json
                    FROM user_characters
                """)
                rows = cursor.fetchall()
                user_builds = {}

                for row in rows:
                    stats_json = row[11] if row[11] else "{}"
                    try:
                        parsed_stats = json.loads(stats_json)
                    except (json.JSONDecodeError, TypeError):
                        parsed_stats = {}

                    user_builds[row[0]] = {
                        "name": row[0],
                        "level": row[1],
                        "constellation": row[2],
                        "weapon": row[3],
                        "weapon_level": row[4],
                        "refinement": row[5],
                        "artifact": row[6],
                        "artifact_2": row[7],
                        "artifact_stats": parsed_stats,
                        "talents": {
                            "attack": row[8],
                            "skill": row[9],
                            "burst": row[10]
                        }
                    }
                return user_builds
        except sqlite3.Error as e:
            raise DatabaseError(f"Fehler beim Laden der Charakter-Builds: {e}") from e

    def save_user_character(self, char_name: str, card_data: dict):
        """Speichert oder aktualisiert das globale Build-Profil eines Charakters in SQLite."""
        try:
            talents = card_data.get("talents", {})
            artifact_stats = json.dumps(card_data.get("artifact_stats", {}), ensure_ascii=False)

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO user_characters (
                        char_name, level, constellation, weapon, weapon_level, refinement,
                        artifact, artifact_2, talent_attack, talent_skill, talent_burst, artifact_stats_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    char_name,
                    card_data.get("level", 90),
                    card_data.get("constellation", 0),
                    card_data.get("weapon", ""),
                    card_data.get("weapon_level", 90),
                    card_data.get("refinement", 1),
                    card_data.get("artifact", ""),
                    card_data.get("artifact_2", ""),
                    talents.get("attack", DEFAULT_TALENTS["attack"]),
                    talents.get("skill", DEFAULT_TALENTS["skill"]),
                    talents.get("burst", DEFAULT_TALENTS["burst"]),
                    artifact_stats
                ))
                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Build für '{char_name}' konnte nicht gespeichert werden: {e}") from e

    # --- IMPORT / EXPORT ---

    def export_user_data(self, path: str):
        """Schreibt Charakter-Builds und Teams (ohne Stammdaten) als JSON-Datei."""
        builds = self.load_user_characters()
        self.load_teams()
        teams = [
            {"name": name, "members": [m.get("name", "") if isinstance(m, dict) else m for m in members]}
            for name, members in self.saved_teams.items()
        ]
        data = {
            "format": EXCHANGE_FORMAT,
            "version": EXCHANGE_VERSION,
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "builds": list(builds.values()),
            "teams": teams,
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            raise DatabaseError(f"Export nach {path} fehlgeschlagen: {e}") from e

    def import_user_data(self, path: str, replace: bool = False) -> dict:
        """Liest eine Export-Datei ein. Gleichnamige Builds/Teams werden überschrieben.

        replace=True löscht vorher alle vorhandenen Builds und Teams. Unbekannte Charaktere werden
        übersprungen. Rückgabe: {"builds": n, "teams": n, "skipped": [Namen]}.
        """
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise DatabaseError(f"Datei konnte nicht gelesen werden: {e}") from e

        if not isinstance(data, dict) or data.get("format") != EXCHANGE_FORMAT:
            raise DatabaseError("Die Datei ist keine Export-Datei des Genshin Team-Managers.")
        if not isinstance(data.get("version"), int) or data["version"] > EXCHANGE_VERSION:
            raise DatabaseError("Die Datei stammt aus einer neueren Version und kann nicht gelesen werden.")

        result = {"builds": 0, "teams": 0, "skipped": []}
        try:
            with self.get_connection() as conn:
                known = {r[0] for r in conn.execute("SELECT name FROM characters")}
                if replace:
                    conn.execute("DELETE FROM teams")
                    conn.execute("DELETE FROM user_characters")

                for b in data.get("builds", []):
                    name = b.get("name") if isinstance(b, dict) else None
                    if name not in known:
                        result["skipped"].append(str(name))
                        continue
                    talents = b.get("talents") or {}
                    stats = b.get("artifact_stats") or {}
                    conn.execute("""
                        INSERT OR REPLACE INTO user_characters (
                            char_name, level, constellation, weapon, weapon_level, refinement,
                            artifact, artifact_2, talent_attack, talent_skill, talent_burst, artifact_stats_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        name, b.get("level", 90), b.get("constellation", 0), b.get("weapon", ""),
                        b.get("weapon_level", 90), b.get("refinement", 1), b.get("artifact", ""),
                        b.get("artifact_2", ""),
                        talents.get("attack", DEFAULT_TALENTS["attack"]),
                        talents.get("skill", DEFAULT_TALENTS["skill"]),
                        talents.get("burst", DEFAULT_TALENTS["burst"]),
                        json.dumps(stats, ensure_ascii=False),
                    ))
                    result["builds"] += 1

                for t in data.get("teams", []):
                    team_name = (t.get("name") or "").strip() if isinstance(t, dict) else ""
                    if not team_name:
                        continue
                    members = []
                    for m in t.get("members", []):
                        if m in known and m not in members:
                            members.append(m)
                        elif m not in known:
                            result["skipped"].append(str(m))
                    conn.execute("INSERT OR IGNORE INTO teams (name) VALUES (?)", (team_name,))
                    team_id = conn.execute("SELECT id FROM teams WHERE name = ?", (team_name,)).fetchone()[0]
                    conn.execute("DELETE FROM team_members WHERE team_id = ?", (team_id,))
                    for slot, m in enumerate(members[:MAX_TEAM_SIZE]):
                        conn.execute(
                            "INSERT INTO team_members (team_id, char_name, slot_order) VALUES (?, ?, ?)",
                            (team_id, m, slot),
                        )
                    result["teams"] += 1
        except (sqlite3.Error, AttributeError, TypeError) as e:
            raise DatabaseError(f"Import fehlgeschlagen, es wurde nichts verändert: {e}") from e

        self.load_teams()
        result["skipped"] = sorted(set(result["skipped"]))
        return result

    # --- HILFSMETHODEN ---

    def get_character_by_name(self, name: str) -> Character:
        """Sucht einen Charakter nach Namen im Speicher oder erzeugt ein Fallback-Objekt."""
        clean_name = name.split("(")[0].strip().lower()

        # 1. Exakter Treffer
        for c in self.available_characters:
            if c.name.lower() == name.lower():
                return c

        # 2. Treffer nach Basisnamen (z.B. "Traveler" für "Traveler (Dendro)")
        for c in self.available_characters:
            if c.name.lower() == clean_name or clean_name in c.name.lower():
                return c

        # Fallback: Automatischen Icon-Pfad aus dem Namen generieren
        fallback_icon = icon_path_for(name)

        return Character(
            name=name,
            element="Anemo",
            weapon_type="Einhandschwert",
            region="Unbekannt",
            rarity=4,
            icon_path=fallback_icon
        )

    def get_weapons_by_type(self, weapon_type: str) -> list[Weapon]:
        """Gibt alle Waffen eines bestimmten Typs zurück."""
        return [w for w in self.available_weapons if w.weapon_type.lower() == weapon_type.lower()]

    def get_artifact_by_name(self, name: str) -> Optional[ArtifactSet]:
        """Sucht ein Artefaktset nach Namen."""
        for a in self.available_artifacts:
            if a.name.lower() == name.lower():
                return a
        return None