import os
from typing import Optional

# Projektverzeichnis: alle Pfade werden relativ hierzu aufgelöst,
# damit die App unabhängig vom aktuellen Arbeitsverzeichnis funktioniert.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "assets", "images")

# Standard-Talentstufen für Charaktere ohne gespeichertes Build (wie in der DB)
DEFAULT_TALENTS = {"attack": 1, "skill": 1, "burst": 1}


def resolve_path(path: str) -> str:
    """Löst einen (in der DB relativ gespeicherten) Pfad gegen das Projektverzeichnis auf."""
    return path if os.path.isabs(path) else os.path.join(BASE_DIR, path)


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
    def __init__(self, name: str, weapon_type: str, rarity: int):
        self.name = name
        self.weapon_type = weapon_type
        self.rarity = rarity

    @property
    def icon_path(self) -> str:
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
