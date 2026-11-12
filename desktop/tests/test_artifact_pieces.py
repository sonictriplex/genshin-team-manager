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


if __name__ == "__main__":
    unittest.main()
