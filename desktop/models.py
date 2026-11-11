import os
from typing import Optional

# Projektverzeichnis: alle Pfade werden relativ hierzu aufgelöst,
# damit die App unabhängig vom aktuellen Arbeitsverzeichnis funktioniert.
# Gemeinsame Versionsnummer von Web, Android und Desktop; zusammen mit CHANGELOG.md hochzählen (ein Test vergleicht beide)
APP_VERSION = "1.6.4"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Gemeinsame Daten für Desktop, Web und weitere Clients (Bilder, Stammdaten)
SHARED_DIR = os.path.join(os.path.dirname(BASE_DIR), "shared")
IMAGES_DIR = os.path.join(SHARED_DIR, "assets", "images")

# Standard-Talentstufen für Charaktere ohne gespeichertes Build (wie in der DB)
DEFAULT_TALENTS = {"attack": 1, "skill": 1, "burst": 1}


def resolve_path(path: str) -> str:
    """Löst einen (in der DB relativ gespeicherten) Pfad gegen das gemeinsame Verzeichnis `shared/` auf."""
    return path if os.path.isabs(path) else os.path.join(SHARED_DIR, path)


def icon_path_for(name: str) -> str:
    """Leitet den Icon-Pfad aus einem Charakter- oder Waffennamen ab.

    Klammerzusätze werden entfernt, z.B. "Traveler (Anemo)" -> traveler.png.
    """
    clean = name.split("(")[0].strip().lower()
    for ch in ("'", "’", "„", "“"):
        clean = clean.replace(ch, "")
    clean = clean.replace(" ", "_").replace("-", "_")
    return os.path.join(IMAGES_DIR, f"{clean}.png")


class Character:
    """Modelliert einen Genshin Impact Charakter."""
    def __init__(
        self,
        name: str,
        element: str,
        weapon_type: str,
        region: str,
        rarity: int,
        icon_path: Optional[str] = None
    ):
        self.name = name
        self.element = element
        self.weapon_type = weapon_type
        self.region = region
        self.rarity = rarity
        self._icon_path = icon_path

    @property
    def icon_path(self) -> str:
        """Pfad zum Charakter-Icon: der in der DB hinterlegte, falls vorhanden, sonst aus dem Namen abgeleitet."""
        if self._icon_path:
            explicit = resolve_path(self._icon_path)
            if os.path.exists(explicit):
                return explicit
        return icon_path_for(self.name)


class Weapon:
    """Modelliert eine Genshin Impact Waffe."""
    def __init__(self, name: str, weapon_type: str, rarity: int, icon_path: Optional[str] = None):
        self.name = name
        self.weapon_type = weapon_type
        self.rarity = rarity
        self._icon_path = icon_path

    @property
    def icon_path(self) -> str:
        if self._icon_path:
            explicit = resolve_path(self._icon_path)
            if os.path.exists(explicit):
                return explicit
        return icon_path_for(self.name)


class ArtifactSet:
    """Modelliert ein Artefaktset inklusive Set-Boni."""
    def __init__(
        self,
        name: str,
        bonus_1pc: str = "",
        bonus_2pc: str = "",
        bonus_4pc: str = ""
    ):
        self.name = name
        self.bonus_1pc = bonus_1pc
        self.bonus_2pc = bonus_2pc
        self.bonus_4pc = bonus_4pc
