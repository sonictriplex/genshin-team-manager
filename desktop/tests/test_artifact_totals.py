"""Tests für die Gesamtwerte der Artefakte im Detailpanel.

Start (im Ordner desktop/):  python -m unittest discover -s tests -v
"""
import os
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
from models import format_stat_total, parse_stat_value, sum_artifact_stats

app = None


def setUpModule():
    global app
    app = QApplication.instance() or QApplication([])


class StatTotalsTest(unittest.TestCase):
    def test_werte_lesen(self):
        self.assertEqual(parse_stat_value("46,6"), 46.6)
        self.assertEqual(parse_stat_value("3.9%"), 3.9)
        self.assertEqual(parse_stat_value("4,780"), 4780)
        self.assertEqual(parse_stat_value("4.780"), 4780)
        self.assertIsNone(parse_stat_value(""))
        self.assertIsNone(parse_stat_value("abc"))

    def test_summe_je_stat_in_fester_reihenfolge(self):
        entries = [("KT%", "31,1"), ("LP (Fix)", "4780"), ("KT%", "3.9"), ("LP (Fix)", "209"),
                   ("ANG%", "abc"), ("", "5"), ("DEF%", "5,8")]
        totals = sum_artifact_stats(entries)
        self.assertEqual([s for s, _ in totals], ["LP (Fix)", "VTD%", "KT%"])   # DEF% wird zu VTD%
        self.assertEqual([format_stat_total(s, t) for s, t in totals], ["4989", "5,8%", "35%"])

    def test_formatierung(self):
        self.assertEqual(format_stat_total("KT%", 38.900000000000006), "38,9%")
        self.assertEqual(format_stat_total("ANG (Fix)", 311), "311")


class TotalsPanelTest(unittest.TestCase):
    def test_panel_summiert_live(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        manager = GenshinManager(os.path.join(tmp.name, "test.db"))
        card = widgets.CharacterCardWidget(manager.get_character_by_name("Furina"), manager, {})
        self.addCleanup(card.deleteLater)
        panel = widgets.ArtifactPanel(card, manager)
        self.addCleanup(panel.deleteLater)
        self.assertIn("Noch keine Werte", panel.totals_label.text())

        panel.slots["Blume"].main_val.setText("4780")
        w = panel.slots["Krone"]
        w.main_val.setText("31,1")
        cb, val = w.subs[0]
        cb.setCurrentIndex(cb.findData("KT%"))
        val.setText("3,9")
        text = panel.totals_label.text()
        self.assertIn("4780", text)
        self.assertIn("35%", text)


if __name__ == "__main__":
    unittest.main()
