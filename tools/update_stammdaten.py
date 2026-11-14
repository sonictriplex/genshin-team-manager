#!/usr/bin/env python3
"""Prüft, ob die Genshin-Stammdaten (Charaktere, Waffen) aktuell sind, und ergänzt Fehlendes.

Quelle: Enka.Network API-Docs (github.com/EnkaNetwork/API-docs, Ordner store/gi) und die Bilder von enka.network.

    python3 tools/update_stammdaten.py            Prüfen (ändert nichts, Exit-Code 1 = es fehlt etwas)
    python3 tools/update_stammdaten.py --apply    Fehlendes ergänzen (fragt vorher nach)
    python3 tools/update_stammdaten.py --apply --yes   ohne Rückfrage

Was --apply macht:
  - trägt neue Charaktere und Waffen in shared/stammdaten.json ein (alphabetisch, ohne Umformatierung)
  - lädt die Bilder nach shared/assets/images (vorhandene Dateien werden nie überschrieben)
  - schreibt eine Migration web/migrations/NNN_stammdaten_<Datum>.sql (INSERT IGNORE) für die Datenbank
Danach: Migration in phpMyAdmin ausführen und deploy/deploy.sh starten. Das Skript deployt nichts selbst.

Regionen: Die Quelle kennt keine Region. Charaktere ohne Eintrag in shared/regionen.json
(oder per --region "Name=Region") werden nur gemeldet und NICHT eingetragen.

Achtung: Die Quelle enthält manchmal Beta-Einträge, die im Spiel noch nicht erschienen sind.
Die Liste der gefundenen Einträge vor dem Ergänzen prüfen (daher die Rückfrage).
"""
import argparse
import datetime
import json
import re
import sys
import urllib.request
from pathlib import Path

RAW = "https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/gi/"
UI = "https://enka.network"
ROOT = Path(__file__).resolve().parents[1]

ELEMENTS = {"Fire": "Pyro", "Water": "Hydro", "Wind": "Anemo", "Electric": "Electro",
            "Grass": "Dendro", "Ice": "Cryo", "Rock": "Geo"}
CHAR_WEAPONS = {"WEAPON_SWORD_ONE_HAND": "Einhandschwert", "WEAPON_CLAYMORE": "Großschwert",
                "WEAPON_POLE": "Stangenwaffe", "WEAPON_BOW": "Bogen", "WEAPON_CATALYST": "Katalysator"}
WEAPON_TYPES = {1: "Einhandschwert", 2: "Großschwert", 3: "Bogen", 4: "Stangenwaffe", 5: "Katalysator"}
QUALITY = {"QUALITY_ORANGE": 5, "QUALITY_PURPLE": 4}
KNOWN_REGIONS = {"Mondstadt", "Liyue", "Inazuma", "Sumeru", "Fontaine", "Natlan", "Snezhnaya", "Andere Welt"}


def fetch_json(name):
    with urllib.request.urlopen(RAW + name, timeout=90) as r:
        return json.load(r)


def norm(name):
    """Vergleichsform: ohne Anführungszeichen, kleingeschrieben."""
    return re.sub(r"[„“”\"'’]", "", name).strip().casefold()


def icon_file(name):
    """Dateiname wie getIconUrl() im Frontend: klein, Leerzeichen -> _, Anführungszeichen/Bindestriche weg."""
    return re.sub(r"['’„“\-]", "", name.split("(")[0].strip().lower().replace(" ", "_")) + ".png"


def clean_game_name(name):
    return re.sub(r"^[„“\"]|[“”\"]$", "", name).strip()


def download(url, target):
    if target.exists():
        return "vorhanden"
    req = urllib.request.Request(url, headers={"User-Agent": "stammdaten-update"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    target.write_bytes(data)
    return "geladen"


def find_new(data):
    avatars, weapons, locs = fetch_json("avatars.json"), fetch_json("weapons.json"), fetch_json("locs.json")
    en, de = locs["en"], locs["de"]

    have_chars = {norm(c["name"]) for c in data["characters"]}
    have_weapons = {norm(w["name"]) for w in data["weapons"]}

    chars = []
    for cid, a in avatars.items():
        # nur reguläre Charaktere: keine Reisenden (Varianten mit "-"), keine Test-/Testversions-IDs
        if "-" in cid or not cid.isdigit() or not (10000002 <= int(cid) < 10000900):
            continue
        name = en.get(str(a.get("NameTextMapHash")), "")
        if not name or name == "Traveler" or "(" in name or norm(name) in have_chars:
            continue
        if a.get("QualityType") not in QUALITY or a.get("Element") not in ELEMENTS or a.get("WeaponType") not in CHAR_WEAPONS:
            continue
        chars.append({"id": cid, "name": name, "element": ELEMENTS[a["Element"]],
                      "weapon_type": CHAR_WEAPONS[a["WeaponType"]], "rarity": QUALITY[a["QualityType"]],
                      "icon": a["SideIconName"].replace("Side_", "")})

    new_weapons = []
    for wid, w in weapons.items():
        name_de = de.get(str(w.get("NameTextMapHash")), "")
        if not name_de or w.get("WeaponType") not in WEAPON_TYPES or not (1 <= w.get("Rarity", 0) <= 5):
            continue
        if norm(name_de) in have_weapons or "(" in name_de:
            continue
        new_weapons.append({"id": wid, "name": clean_game_name(name_de), "weapon_type": WEAPON_TYPES[w["WeaponType"]],
                            "rarity": w["Rarity"], "icon": w["Icon"]})
    return sorted(chars, key=lambda c: c["name"].lower()), sorted(new_weapons, key=lambda w: w["name"].lower())


def insert_sorted(items, entry):
    i = next((k for k, x in enumerate(items) if x["name"].lower() > entry["name"].lower()), len(items))
    items.insert(i, entry)


def sql(v):
    return "NULL" if v is None else str(v) if isinstance(v, int) else "'" + str(v).replace("\\", "\\\\").replace("'", "''") + "'"


def next_migration(date):
    nums = [int(m.group(1)) for p in (ROOT / "web" / "migrations").glob("*.sql") if (m := re.match(r"(\d+)_", p.name))]
    return ROOT / "web" / "migrations" / f"{max(nums, default=0) + 1:03d}_stammdaten_{date}.sql"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="Fehlendes ergänzen (Standard: nur prüfen)")
    ap.add_argument("--yes", action="store_true", help="bei --apply nicht nachfragen")
    ap.add_argument("--region", action="append", default=[], metavar="NAME=REGION",
                    help="Region eines neuen Charakters (mehrfach möglich)")
    args = ap.parse_args()

    path = ROOT / "shared" / "stammdaten.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    regions_path = ROOT / "shared" / "regionen.json"
    regions = json.loads(regions_path.read_text(encoding="utf-8")) if regions_path.exists() else {}
    for item in args.region:
        n, _, r = item.partition("=")
        regions[n.strip()] = r.strip()

    print("Lade Daten von Enka.Network …")
    chars, weapons = find_new(data)
    print(f"Stand: {len(data['characters'])} Charaktere, {len(data['weapons'])} Waffen in den Stammdaten.\n")

    ready = [c for c in chars if regions.get(c["name"])]
    no_region = [c for c in chars if not regions.get(c["name"])]
    for c in ready:
        c["region"] = regions[c["name"]]
        if c["region"] not in KNOWN_REGIONS:
            print(f"Hinweis: Region „{c['region']}“ ({c['name']}) ist dem Filter in index.html eventuell noch unbekannt.")

    print(f"Neue Charaktere mit bekannter Region: {len(ready)}")
    for c in ready:
        print(f"  + {c['name']:<20} {c['rarity']}★ {c['element']:<8} {c['weapon_type']:<13} {c['region']}")
    print(f"Neue Charaktere OHNE Region (werden nicht eingetragen): {len(no_region)}")
    for c in no_region:
        print(f"  ? {c['name']:<20} {c['rarity']}★ {c['element']:<8} {c['weapon_type']}")
    if no_region:
        print("  -> Regionen in shared/regionen.json ({\"Name\": \"Region\"}) eintragen oder --region \"Name=Region\" angeben.")
    print(f"Neue Waffen: {len(weapons)}")
    for w in weapons:
        print(f"  + {w['name']:<45} {w['rarity']}★ {w['weapon_type']}")

    if not (ready or weapons or no_region):
        print("\nAlles aktuell.")
        return 0
    if not args.apply:
        print("\nNichts geändert (Prüfmodus). Zum Ergänzen: --apply")
        return 1
    if not (ready or weapons):
        print("\nNichts zu ergänzen: Es fehlen nur Regionen.")
        return 1
    if not args.yes and input("\nDiese Einträge ergänzen? Beta-Einträge vorher prüfen. [j/N] ").strip().lower() not in ("j", "ja", "y"):
        print("Abgebrochen.")
        return 1

    images = ROOT / "shared" / "assets" / "images"
    for c in ready:
        file = icon_file(c["name"])
        try:
            print(f"  Bild {file}: {download(UI + '/ui/' + c['icon'].lstrip('/').removeprefix('ui/'), images / file)}")
        except Exception as e:
            print(f"  Bild {file}: FEHLER ({e})")
        insert_sorted(data["characters"], {"name": c["name"], "element": c["element"], "weapon_type": c["weapon_type"],
                                           "region": c["region"], "rarity": c["rarity"], "icon_path": f"assets/images/{file}"})
    for w in weapons:
        file = icon_file(w["name"])
        try:
            print(f"  Bild {file}: {download(UI + w['icon'], images / file)}")
        except Exception as e:
            print(f"  Bild {file}: FEHLER ({e})")
        insert_sorted(data["weapons"], {"name": w["name"], "weapon_type": w["weapon_type"], "rarity": w["rarity"],
                                        "icon_path": f"assets/images/{file}", "passive": None})

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = ["-- Erzeugt von tools/update_stammdaten.py. Einmal in phpMyAdmin ausführen (INSERT IGNORE, wiederholbar).",
             "-- Passiv-Beschreibungen der neuen Waffen liefert die Quelle nicht (passive_json bleibt NULL)."]
    if ready:
        rows = ",\n".join(f"  ({sql(c['name'])}, {sql(c['element'])}, {sql(c['weapon_type'])}, {sql(c['region'])}, {c['rarity']}, "
                          f"{sql('assets/images/' + icon_file(c['name']))})" for c in ready)
        lines.append("INSERT IGNORE INTO characters (name, element, weapon_type, region, rarity, icon_path) VALUES\n" + rows + ";")
    if weapons:
        rows = ",\n".join(f"  ({sql(w['name'])}, {sql(w['weapon_type'])}, {w['rarity']}, NULL)" for w in weapons)
        lines.append("INSERT IGNORE INTO weapons (name, weapon_type, rarity, passive_json) VALUES\n" + rows + ";")
    migration = next_migration(datetime.date.today().strftime("%Y%m%d"))
    migration.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\nErgänzt: {len(ready)} Charaktere, {len(weapons)} Waffen.")
    print(f"Migration: {migration.relative_to(ROOT)}")
    print("Nächste Schritte: Migration in phpMyAdmin ausführen, dann deploy/deploy.sh.")
    return 1 if no_region else 0


if __name__ == "__main__":
    sys.exit(main())
