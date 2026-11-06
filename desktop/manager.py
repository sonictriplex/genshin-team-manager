import json
import os
import sqlite3
from typing import Optional
from models import Character, Weapon, ArtifactSet, BASE_DIR, DEFAULT_TALENTS, icon_path_for
from seed import SEED_PATH, import_seed, is_seeded

DB_PATH = os.path.join(BASE_DIR, "genshin_manager.db")

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
    rarity INTEGER NOT NULL
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
        except sqlite3.Error as e:
            raise DatabaseError(f"Datenbank konnte nicht initialisiert werden ({self.db_path}): {e}") from e

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
                    SELECT name, weapon_type, rarity 
                    FROM weapons ORDER BY name ASC
                """)
                rows = cursor.fetchall()
                self.available_weapons = [
                    Weapon(name=row[0], weapon_type=row[1], rarity=row[2])
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