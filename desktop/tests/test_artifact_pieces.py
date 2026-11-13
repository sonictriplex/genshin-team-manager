"""Tests für die Namen der Artefaktteile (Dropdown im Detailpanel, Stammdaten, Migration).

Start (im Ordner desktop/):  python -m unittest discover -s tests -v
"""
import json
import os
import sqlite3
import sys
import tempfile
import unittest
import warnings

warnings.simplefilter("ignore", ResourceWarning)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from PySide6.QtWidgets import QApplication

import widgets
from manager import GenshinManager
from models import SHARED_DIR
from seed import SEED_PATH, export_seed

app = None


def setUpModule():
    global app
    app = QApplication.instance() or QApplication([])


class ArtifactPiecesTest(unittest.TestCase):
    def setUp(self):
        warnings.simplefilter("ignore", ResourceWarning)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = os.path.join(self.tmp.name, "test.db")
        self.manager = GenshinManager(self.db)

    def panel(self, saved=None):
        card = widgets.CharacterCardWidget(self.manager.get_character_by_name("Furina"), self.manager, saved or {})
        self.addCleanup(card.deleteLater)
        panel = widgets.ArtifactPanel(card, self.manager)
        self.addCleanup(panel.deleteLater)
        return card, panel

    def test_stammdaten_haben_teilnamen(self):
        with open(SEED_PATH, encoding="utf-8") as f:
            sets = json.load(f)["artifacts"]
        mit_teilen = [a for a in sets if a["pieces"]]
        self.assertGreaterEqual(len(mit_teilen), 60)
        self.assertEqual(self.manager.get_artifact_by_name("Abenteurer").pieces["Feder"], "Abenteurerschwanzfeder")

    def test_optionen_set_teile_zuerst_dann_alle_anderen(self):
        opts = self.manager.piece_options("Feder", ["Abenteurer"])
        self.assertEqual(opts[0], ("Abenteurerschwanzfeder", True))
        self.assertTrue(all(not in_set for _, in_set in opts[1:]))
        self.assertIn(("Zuflucht des Gladiators", False), opts)   # Off-Piece aus einem fremden Set
        names = [n for n, _ in opts[1:]]
        self.assertEqual(names, sorted(names, key=str.casefold))

    def test_einzelteil_sets_nur_bei_krone(self):
        self.assertEqual(list(self.manager.get_artifact_by_name("Wasseropfer").pieces), ["Krone"])
        self.assertNotIn("Wasseropferdiadem", [n for n, _ in self.manager.piece_options("Blume", [])])
        self.assertIn("Wasseropferdiadem", [n for n, _ in self.manager.piece_options("Krone", [])])

    def test_panel_speichert_und_liest_teil_zurueck(self):
        card, panel = self.panel({"artifact": "Abenteurer"})
        w = panel.slots["Feder"]
        w.piece.setCurrentText("Zuflucht des Gladiators")
        stats = panel.get_stats()
        self.assertEqual(stats["Feder"]["piece"], "Zuflucht des Gladiators")
        self.assertEqual(stats["Blume"]["piece"], "")
        _, panel2 = self.panel({"artifact_stats": stats})
        self.assertEqual(panel2.get_stats()["Feder"]["piece"], "Zuflucht des Gladiators")

    def test_freitext_ohne_treffer_zaehlt_als_leer(self):
        _, panel = self.panel()
        panel.slots["Kelch"].piece.setCurrentText("irgendwas")
        self.assertEqual(panel.get_stats()["Kelch"]["piece"], "")

    def test_setwechsel_sortiert_um_und_behaelt_auswahl(self):
        card, panel = self.panel({"artifact": "Abenteurer"})
        panel.slots["Feder"].piece.setCurrentText("Zuflucht des Gladiators")
        widgets.select_value(card.art_combo, "Verbeugung des Gladiators")
        combo = panel.slots["Feder"].piece
        self.assertEqual(combo.itemText(1), "Zuflucht des Gladiators")
        self.assertEqual(panel.get_stats()["Feder"]["piece"], "Zuflucht des Gladiators")

    def test_unbekanntes_gespeichertes_teil_bleibt_erhalten(self):
        _, panel = self.panel({"artifact_stats": {"Blume": {"piece": "Neues Teil"}}})
        self.assertEqual(panel.get_stats()["Blume"]["piece"], "Neues Teil")

    def test_altes_build_ohne_piece_gilt_nicht_als_geaendert(self):
        defaults = widgets.ArtifactPanel.default_stats("Hydro")
        alt = {slot: {k: v for k, v in vals.items() if k != "piece"} for slot, vals in defaults.items()}
        self.assertEqual(widgets.normalize_build({"artifact_stats": alt}, "Hydro")["artifact_stats"], {})

    def test_migration_aelterer_datenbank_fuellt_teilnamen(self):
        old = os.path.join(self.tmp.name, "alt.db")
        with sqlite3.connect(old) as conn:
            conn.execute("CREATE TABLE artifacts (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, "
                         "bonus_1pc TEXT DEFAULT '', bonus_2pc TEXT DEFAULT '', bonus_4pc TEXT DEFAULT '')")
            conn.execute("INSERT INTO artifacts (name) VALUES ('Abenteurer')")
        manager = GenshinManager(old, seed_path=None)
        self.assertEqual(manager.get_artifact_by_name("Abenteurer").pieces, {})   # ohne Seed-Datei: leer, kein Fehler
        os.remove(old)
        with sqlite3.connect(old) as conn:
            conn.execute("CREATE TABLE artifacts (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, "
                         "bonus_1pc TEXT DEFAULT '', bonus_2pc TEXT DEFAULT '', bonus_4pc TEXT DEFAULT '')")
            conn.execute("INSERT INTO artifacts (name) VALUES ('Abenteurer')")
        manager = GenshinManager(old)
        self.assertEqual(manager.get_artifact_by_name("Abenteurer").pieces["Blume"], "Blume eines Abenteurers")

    def test_export_roundtrip_behaelt_pieces(self):
        out = os.path.join(self.tmp.name, "seed.json")
        with sqlite3.connect(self.db) as conn:
            export_seed(conn, out)
        with open(out, encoding="utf-8") as f, open(SEED_PATH, encoding="utf-8") as g:
            self.assertEqual(json.load(f)["artifacts"], json.load(g)["artifacts"])


class BonusTooltipTest(unittest.TestCase):
    setUp = ArtifactPiecesTest.setUp
    """Tooltips mit den Beschreibungen der Set-Boni und Waffen-Passive."""

    def card(self, saved=None, name="Furina"):
        card = widgets.CharacterCardWidget(self.manager.get_character_by_name(name), self.manager, saved or {})
        self.addCleanup(card.deleteLater)
        return card

    def test_artefaktset_tooltip_in_combo_und_auswahlliste(self):
        card = self.card({"artifact": "Verbeugung des Gladiators"})
        self.assertIn("2er-Bonus", card.art_combo.toolTip())
        self.assertIn("4er-Bonus", card.art_combo.toolTip())
        idx = card.art_combo.findData("Abenteurer")
        self.assertIn("max. LP", card.art_combo.itemData(idx, widgets.Qt.ToolTipRole))
        self.assertEqual(card.art_combo_2.itemData(0, widgets.Qt.ToolTipRole), None)   # Platzhalter ohne Tooltip

    def test_waffen_tooltip_folgt_der_veredelung(self):
        weapon = next(w for w in self.manager.available_weapons if w.passive and len(w.passive["text"]) == 5)
        card = self.card({"weapon": weapon.name, "refinement": 1}, name=next(
            c.name for c in self.manager.available_characters if c.weapon_type == weapon.weapon_type))
        self.assertIn("Veredelung 1", card.wpn_input.toolTip())
        self.assertIn(weapon.passive["text"][0].split(".")[0][:30], card.wpn_input.toolTip())
        card.refine_row.buttons[5].click()
        self.assertIn("Veredelung 5", card.wpn_input.toolTip())

    def test_waffe_ohne_passiv_zeigt_den_namen(self):
        weapon = next(w for w in self.manager.available_weapons if not w.passive)
        card = self.card({"weapon": weapon.name}, name=next(
            c.name for c in self.manager.available_characters if c.weapon_type == weapon.weapon_type))
        self.assertEqual(card.wpn_input.toolTip(), weapon.name)

    def test_suchdialog_zeilen_haben_den_passiv_tooltip(self):
        from dialogs import WeaponSearchDialog
        dialog = WeaponSearchDialog(self.manager.available_weapons)
        self.addCleanup(dialog.deleteLater)
        row = next(i for i, w in enumerate(dialog.filtered) if w.passive)
        self.assertIn("Veredelung 1", dialog.table.item(row, 1).toolTip())

    def test_texte_im_tooltip_werden_maskiert(self):
        from models import tooltip_html
        self.assertIn("&lt;b&gt;", tooltip_html("Name", ["<b>x</b>"]))

    def test_migration_aelterer_datenbank_fuellt_passive(self):
        old = os.path.join(self.tmp.name, "alt2.db")
        with sqlite3.connect(old) as conn:
            conn.execute("CREATE TABLE weapons (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, "
                         "weapon_type TEXT NOT NULL, rarity INTEGER NOT NULL, icon_path TEXT)")
            conn.execute("INSERT INTO weapons (name, weapon_type, rarity) VALUES ('Silberlampe', 'Einhandschwert', 5)")
        manager = GenshinManager(old)
        self.assertEqual(manager.get_weapon_by_name("Silberlampe").passive["name"], "Sonnenspiegelung im Wasser")

    def test_export_roundtrip_behaelt_waffen_passive(self):
        out = os.path.join(self.tmp.name, "seed2.json")
        with sqlite3.connect(self.db) as conn:
            export_seed(conn, out)
        with open(out, encoding="utf-8") as f, open(SEED_PATH, encoding="utf-8") as g:
            self.assertEqual(json.load(f)["weapons"], json.load(g)["weapons"])


class StatNamesTest(unittest.TestCase):
    setUp = ArtifactPiecesTest.setUp
    """DEF% / DEF (Fix) heißen jetzt VTD% / VTD (Fix); ältere Builds werden umgewandelt."""

    LEGACY = {"Sanduhr": {"main_stat": "DEF%", "main_value": "58,3",
                          "substats": [{"stat": "DEF (Fix)", "val": "21"}, {"stat": "KT%", "val": "3,9"}] + [{}] * 2}}

    def test_auswahllisten_kennen_vtd_und_kein_def(self):
        self.assertIn("VTD%", dict(widgets.ArtifactPanel.SLOTS)["Sanduhr"])
        self.assertIn("VTD (Fix)", widgets.ArtifactPanel.SUBSTATS)
        self.assertFalse([s for s in widgets.ArtifactPanel.SUBSTATS if s.startswith("DEF")])
        self.assertFalse([m for _, mains in widgets.ArtifactPanel.SLOTS for m in mains if m.startswith("DEF")])

    def test_panel_wandelt_alte_namen_um(self):
        card = widgets.CharacterCardWidget(self.manager.get_character_by_name("Furina"), self.manager,
                                           {"artifact_stats": self.LEGACY})
        self.addCleanup(card.deleteLater)
        stats = widgets.ArtifactPanel(card, self.manager).get_stats()["Sanduhr"]
        self.assertEqual(stats["main_stat"], "VTD%")
        self.assertEqual([s["stat"] for s in stats["substats"]], ["VTD (Fix)", "KT%", "", ""])

    def test_start_migriert_gespeicherte_builds(self):
        self.manager.save_user_character("Furina", {"artifact_stats": self.LEGACY})
        with sqlite3.connect(self.db) as conn:
            conn.execute("UPDATE user_characters SET artifact_stats_json = REPLACE(artifact_stats_json, 'VTD', 'DEF')")   # Altbestand nachstellen
            self.assertIn('"DEF%"', conn.execute("SELECT artifact_stats_json FROM user_characters").fetchone()[0])
        manager = GenshinManager(self.db)
        sanduhr = manager.load_user_characters()["Furina"]["artifact_stats"]["Sanduhr"]
        self.assertEqual(sanduhr["main_stat"], "VTD%")
        self.assertEqual(sanduhr["substats"][0]["stat"], "VTD (Fix)")

    def test_import_alter_datei_wandelt_um(self):
        path = os.path.join(self.tmp.name, "alt.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"format": "genshin-team-manager", "version": 1,
                       "builds": [{"name": "Furina", "artifact_stats": self.LEGACY}], "teams": []}, f)
        self.manager.import_user_data(path)
        sanduhr = self.manager.load_user_characters()["Furina"]["artifact_stats"]["Sanduhr"]
        self.assertEqual(sanduhr["main_stat"], "VTD%")


if __name__ == "__main__":
    unittest.main()
