import os
from typing import Any, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from models import Character, Weapon

WEAPON_TYPES = ["Einhandschwert", "Großschwert", "Stangenwaffe", "Bogen", "Katalysator"]
REGIONS = ["Mondstadt", "Liyue", "Inazuma", "Sumeru", "Fontaine", "Natlan",
           "Snezhnaya", "Nod-Krai", "Andere Welt", "Sonstige"]
ELEMENTS = ["Anemo", "Geo", "Electro", "Dendro", "Hydro", "Pyro", "Cryo", "Adaptive"]


class SearchDialog(QDialog):
    """Basisklasse für Such-/Auswahldialoge mit Textsuche, Filtern und Tabelle.

    Unterklassen definieren `create_filters()`, `matches()` und `row_values()`.
    """
    HEADERS: list[str] = []
    ICON_SIZE = 32

    def __init__(self, items: list, title: str, search_placeholder: str,
                 select_label: str, noun: str, parent=None):
        super().__init__(parent)
        self.items = items
        self.filtered: list = []
        self.selected: Optional[Any] = None
        self.noun = noun

        self.setWindowTitle(title)
        layout = QVBoxLayout(self)

        self.filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(search_placeholder)
        self.search_input.textChanged.connect(self.apply_filters)
        self.filter_layout.addWidget(self.search_input)
        self.create_filters()
        layout.addLayout(self.filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setIconSize(QSize(self.ICON_SIZE, self.ICON_SIZE))
        header = self.table.horizontalHeader()
        for col in range(len(self.HEADERS)):
            header.setSectionResizeMode(col, QHeaderView.Stretch if col == 1 else QHeaderView.ResizeToContents)
        self.table.doubleClicked.connect(self.accept_selection)
        layout.addWidget(self.table)

        bottom_layout = QHBoxLayout()
        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        bottom_layout.addWidget(self.status_label)
        bottom_layout.addStretch()
        btn_select = QPushButton(select_label)
        btn_select.clicked.connect(self.accept_selection)
        bottom_layout.addWidget(btn_select)
        layout.addLayout(bottom_layout)

        self.apply_filters()

    # --- von Unterklassen zu implementieren ---

    def create_filters(self):
        pass

    def matches(self, item) -> bool:
        raise NotImplementedError

    def row_values(self, item) -> tuple[str, list[str]]:
        """Liefert (Icon-Pfad, Spaltentexte ab Spalte 1)."""
        raise NotImplementedError

    # --- Hilfsmethoden ---

    def add_filter_combo(self, all_label: str, values: list, fmt=str) -> QComboBox:
        """Fügt einen Filter hinzu. Der erste Eintrag ("Alle …") hat keinen Wert und filtert nicht."""
        combo = QComboBox()
        combo.addItem(all_label, None)
        for value in values:
            combo.addItem(fmt(value), value)
        combo.currentIndexChanged.connect(self.apply_filters)
        self.filter_layout.addWidget(combo)
        return combo

    @staticmethod
    def filter_ok(combo: QComboBox, value) -> bool:
        wanted = combo.currentData()
        return wanted is None or wanted == value

    def search_ok(self, name: str) -> bool:
        text = self.search_input.text().lower().strip()
        return not text or text in name.lower()

    # --- Logik ---

    def apply_filters(self):
        self.filtered = [item for item in self.items if self.matches(item)]
        self.update_table()

    def update_table(self):
        self.table.setRowCount(len(self.filtered))
        last_col = len(self.HEADERS) - 1
        for row, item in enumerate(self.filtered):
            icon_path, texts = self.row_values(item)
            icon_item = QTableWidgetItem()
            if os.path.exists(icon_path):
                icon_item.setIcon(QIcon(icon_path))
            self.table.setItem(row, 0, icon_item)

            for col, text in enumerate(texts, start=1):
                cell = QTableWidgetItem(text)
                if col == last_col:
                    cell.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, cell)

        self.status_label.setText(f"{len(self.filtered)} {self.noun} gefunden")

    def accept_selection(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.filtered):
            self.selected = self.filtered[row]
            self.accept()


class WeaponSearchDialog(SearchDialog):
    """Dialog zur Suche und Filterung von Waffen inklusive Icons."""
    HEADERS = ["", "Name", "Typ", "Seltenheit"]
    ICON_SIZE = 32

    def __init__(self, weapons: list[Weapon], weapon_type_filter: Optional[str] = None, parent=None):
        self.preset_type = weapon_type_filter
        super().__init__(weapons, "Waffe auswählen", "Waffennamen suchen...",
                         "Waffe übernehmen", "Waffen", parent)
        self.resize(650, 500)

    def create_filters(self):
        self.type_filter = self.add_filter_combo("Alle Typen", WEAPON_TYPES)
        self.rarity_filter = self.add_filter_combo("Alle Seltenheiten", [5, 4, 3, 2, 1], lambda r: f"{r} ★")
        if self.preset_type:
            # Signale blockieren: gefiltert wird erst am Ende von SearchDialog.__init__
            self.type_filter.blockSignals(True)
            select_idx = self.type_filter.findData(self.preset_type)
            self.type_filter.setCurrentIndex(max(select_idx, 0))
            self.type_filter.blockSignals(False)

    def matches(self, w: Weapon) -> bool:
        return (self.search_ok(w.name)
                and self.filter_ok(self.type_filter, w.weapon_type)
                and self.filter_ok(self.rarity_filter, w.rarity))

    def row_values(self, w: Weapon):
        return w.icon_path, [w.name, w.weapon_type, f"{w.rarity} ★"]


class CharacterSearchDialog(SearchDialog):
    """Dialog zur Suche und Filterung von Charakteren nach Region, Element und Seltenheit."""
    HEADERS = ["", "Name", "Element", "Waffe", "Region", "Seltenheit"]
    ICON_SIZE = 36

    def __init__(self, characters: list[Character], parent=None):
        super().__init__(characters, "Charakter auswählen", "Charakter suchen...",
                         "Charakter auswählen", "Charaktere", parent)
        self.resize(750, 520)

    def create_filters(self):
        self.region_filter = self.add_filter_combo("Alle Regionen", REGIONS)
        self.element_filter = self.add_filter_combo("Alle Elemente", ELEMENTS)
        self.rarity_filter = self.add_filter_combo("Alle Seltenheiten", [5, 4], lambda r: f"{r} ★")

    def matches(self, c: Character) -> bool:
        return (self.search_ok(c.name)
                and self.filter_ok(self.region_filter, c.region)
                and self.filter_ok(self.element_filter, c.element)
                and self.filter_ok(self.rarity_filter, c.rarity))

    def row_values(self, c: Character):
        return c.icon_path, [c.name, c.element, c.weapon_type, c.region, f"{c.rarity} ★"]
