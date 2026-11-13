import html
import os
import re
from typing import Optional

# Projektverzeichnis: alle Pfade werden relativ hierzu aufgelöst,
# damit die App unabhängig vom aktuellen Arbeitsverzeichnis funktioniert.
# Gemeinsame Versionsnummer von Web, Android und Desktop; zusammen mit CHANGELOG.md hochzählen (ein Test vergleicht beide)
APP_VERSION = "1.7.3"

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


# Vor der Umbenennung gespeicherte Stats: DEF heißt jetzt VTD (Verteidigung)
LEGACY_STAT_NAMES = {"DEF%": "VTD%", "DEF (Fix)": "VTD (Fix)"}


def current_stat_name(stat):
    """Aktueller Name eines Stats (alte Namen werden umgewandelt, alles andere bleibt unverändert)."""
    return LEGACY_STAT_NAMES.get(stat, stat) if isinstance(stat, str) else stat


def rename_legacy_stats(stats):
    """Kopie von artifact_stats, in der Haupt- und Substats die aktuellen Namen tragen."""
    if not isinstance(stats, dict):
        return stats
    result = {}
    for slot_name, slot in stats.items():
        if isinstance(slot, dict):
            slot = dict(slot)
            if "main_stat" in slot:
                slot["main_stat"] = current_stat_name(slot["main_stat"])
            if isinstance(slot.get("substats"), list):
                slot["substats"] = [
                    {**sub, "stat": current_stat_name(sub.get("stat"))} if isinstance(sub, dict) and "stat" in sub else sub
                    for sub in slot["substats"]
                ]
        result[slot_name] = slot
    return result


STAT_TOTAL_ORDER = ["LP%", "LP (Fix)", "ANG%", "ANG (Fix)", "VTD%", "VTD (Fix)",
                    "Elementarkunde", "Aufladerate", "KT%", "KSCH%", "Heilungsbonus%"]


def parse_stat_value(text) -> Optional[float]:
    """Zahl aus einem Freitext-Wert ("46,6", "3.9%", "4.780"); None, wenn keine Zahl erkennbar ist."""
    t = re.sub(r"\s", "", str(text if text is not None else "")).replace("%", "")
    if not t:
        return None
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", t):   # "4,780" ist ein Tausenderpunkt, "46,6" ein Komma
        t = re.sub(r"[.,]", "", t)
    try:
        return float(t.replace(",", "."))
    except ValueError:
        return None


def sum_artifact_stats(entries) -> list[tuple[str, float]]:
    """Summiert [(stat, wert)] je Stat; Einträge ohne Stat oder Zahl entfallen. Feste Reihenfolge, Rest alphabetisch."""
    sums: dict[str, float] = {}
    for stat, value in entries:
        stat = current_stat_name(stat or "")
        number = parse_stat_value(value)
        if not stat or number is None:
            continue
        sums[stat] = sums.get(stat, 0.0) + number
    rank = lambda stat: STAT_TOTAL_ORDER.index(stat) if stat in STAT_TOTAL_ORDER else len(STAT_TOTAL_ORDER)
    return sorted(sums.items(), key=lambda kv: (rank(kv[0]), kv[0]))


def format_stat_total(stat: str, total: float) -> str:
    rounded = round(total, 1)
    text = str(int(rounded)) if rounded == int(rounded) else f"{rounded:.1f}".replace(".", ",")
    return text + "%" if stat.endswith("%") else text


def tooltip_html(title: str, paragraphs: list[str]) -> str:
    """Tooltip mit fester Breite (Qt bricht Rich-Text-Tooltips sonst nicht um). Texte werden maskiert."""
    body = "".join(f"<p style='margin-top:6px; margin-bottom:0'>{html.escape(p).replace(chr(10), '<br>')}</p>"
                   for p in paragraphs if p)
    return f"<table width='340'><tr><td><b>{html.escape(title)}</b>{body}</td></tr></table>"


class Weapon:
    """Modelliert eine Genshin Impact Waffe."""
    def __init__(self, name: str, weapon_type: str, rarity: int, icon_path: Optional[str] = None,
                 passive: Optional[dict] = None):
        self.name = name
        self.weapon_type = weapon_type
        self.rarity = rarity
        self._icon_path = icon_path
        # {"name": Name des Passivs, "text": [Beschreibung je Veredelung 1..5]} oder None (z. B. Anfängerwaffen)
        self.passive = passive if isinstance(passive, dict) else None

    def passive_tooltip(self, refinement: int = 1) -> str:
        """Beschreibung des Waffen-Passivs bei der gegebenen Veredelung (1–5), sonst leer."""
        texts = (self.passive or {}).get("text") or []
        if not texts:
            return ""
        step = max(1, min(refinement, len(texts)))
        return tooltip_html(self.name, [f"{self.passive.get('name', '')} (Veredelung {step})", texts[step - 1]])

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
        bonus_4pc: str = "",
        pieces: Optional[dict] = None
    ):
        self.name = name
        self.pieces = pieces or {}  # Slotname (Blume, Feder, ...) -> Name des Teils
        self.bonus_1pc = bonus_1pc
        self.bonus_2pc = bonus_2pc
        self.bonus_4pc = bonus_4pc

    def bonus_tooltip(self) -> str:
        """Set-Boni (1er, 2er, 4er) als Tooltip, leer wenn das Set keine Beschreibung hat."""
        parts = [f"{label}-Bonus: {bonus}" for label, bonus in
                 (("1er", self.bonus_1pc), ("2er", self.bonus_2pc), ("4er", self.bonus_4pc)) if bonus]
        return tooltip_html(self.name, parts) if parts else ""
