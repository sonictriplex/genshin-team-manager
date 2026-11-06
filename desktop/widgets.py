import os
from dataclasses import dataclass
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QComboBox, QPushButton, QSpinBox, QLineEdit, QMessageBox, QDialog, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from models import Character, ArtifactSet, DEFAULT_TALENTS
from manager import GenshinManager, DatabaseError
from dialogs import WeaponSearchDialog
from styles import element_badge_style, set_selected, tint_style


# --- Hilfsfunktionen ---

def combo_value(combo: QComboBox) -> str:
    """Liefert den Wert einer ComboBox: die Item-Daten falls gesetzt (Platzhalter -> ""), sonst den Text."""
    data = combo.currentData()
    return data if data is not None else combo.currentText()


def select_value(combo: QComboBox, value: str):
    """Wählt den Eintrag mit passendem Wert (Daten oder Text); sonst den ersten Eintrag."""
    idx = combo.findData(value)
    if idx < 0:
        idx = combo.findText(value)
    combo.setCurrentIndex(max(idx, 0))


def show_db_error(parent: QWidget, error: Exception):
    """Zeigt einen Datenbankfehler als Dialog an."""
    QMessageBox.critical(parent, "Datenbankfehler", str(error))


def section_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("sectionTitle")
    return label


def muted(text: str) -> QLabel:
    return QLabel(f"<span style='color:#7a788e; font-size:10px;'>{text}</span>")


def normalize_build(build: dict, element: Optional[str] = None) -> dict:
    """Bringt ein Build in eine vergleichbare Form.

    `element` ist das Element des Charakters (bestimmt den Standard-Hauptwert des Kelchs).

    Artefakt-Slots mit Standardwerten zählen als nicht vorhanden, damit z.B. "nie ausgefüllt"
    und "Detailansicht geöffnet, nichts eingetragen" als gleich erkannt werden.
    """
    defaults = ArtifactPanel.default_stats(element)
    stats = {
        slot: values for slot, values in (build.get("artifact_stats") or {}).items()
        if values != defaults.get(slot)
    }
    return {**build, "artifact_stats": stats}


# --- Kleine Widgets ---

class ClickableLineEdit(QLineEdit):
    """Schreibgeschütztes QLineEdit, das bei einem Klick ein Signal auslöst."""
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ChoiceButtonRow(QHBoxLayout):
    """Reihe von Auswahl-Buttons (z.B. C0–C6 oder Veredelung 1–5), genau einer ist ausgewählt."""

    def __init__(self, label: str, values: range, fmt=str, width: int = 24, selected: int = 0):
        super().__init__()
        self.setSpacing(3)
        title = QLabel(f"<b>{label}</b>")
        title.setObjectName("choiceLabel")
        self.addWidget(title)

        self.value = selected
        self.buttons: dict[int, QPushButton] = {}
        for val in values:
            btn = QPushButton(fmt(val))
            btn.setObjectName("choiceButton")
            btn.setFixedSize(width, 20)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, v=val: self.select(v))
            self.buttons[val] = btn
            self.addWidget(btn)
        self.addStretch()
        self.select(selected)

    def select(self, value: int):
        self.value = value
        for val, btn in self.buttons.items():
            set_selected(btn, val == value)


class AddCharacterSlotWidget(QFrame):
    """Platzhalter-Karte zum Hinzufügen eines neuen Charakters."""
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        plus_icon = QLabel("+")
        plus_icon.setObjectName("addSlotPlus")
        plus_icon.setAlignment(Qt.AlignCenter)

        text_label = QLabel("Charakter hinzufügen")
        text_label.setObjectName("addSlotText")
        text_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(plus_icon)
        layout.addWidget(text_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()


# --- Charakterkarte ---

class CharacterCardWidget(QFrame):
    """Charakterkarte mit Level, Sternbildern, Waffe, Artefakten und Talenten."""
    close_requested = Signal(object)
    toggle_detail_requested = Signal(object, bool)

    def __init__(self, character: Character, manager: GenshinManager, saved_data: dict = None, parent=None):
        super().__init__(parent)
        self.character = character
        self.manager = manager
        self.saved_data = saved_data or {}
        self.is_detail_open = False
        # Gesetzt, solange das Artefakt-Detailpanel dieser Karte angezeigt wird
        self.artifact_panel: Optional["ArtifactPanel"] = None
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(tint_style("CharacterCardWidget", self.character.element))
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 10)
        main_layout.setSpacing(6)

        main_layout.addWidget(self._build_header())

        # Die Blöcke (Info/Sternbild, Waffe, Artefakte, Talente) sind Gruppen. Zusätzlicher Platz wird
        # gleichmäßig auf die Lücken zwischen den Gruppen verteilt, sodass unter dem letzten Block
        # derselbe Abstand bleibt wie links und rechts (10 px).
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(10, 4, 10, 0)
        info_layout.setSpacing(0)
        builders = (self._build_info, self._build_weapon, self._build_artifacts, self._build_talents)
        for i, build in enumerate(builders):
            if i:
                info_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
            group = QVBoxLayout()
            group.setSpacing(10)
            build(group)
            info_layout.addLayout(group)
        main_layout.addLayout(info_layout, stretch=1)

    def _build_header(self) -> QFrame:
        header_frame = QFrame()
        header_frame.setObjectName("cardHeader")
        header_frame.setProperty("rarity", str(self.character.rarity))
        header_frame.setFixedHeight(140)

        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 8, 8, 8)
        header_layout.setSpacing(0)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)

        rarity_badge = QLabel(f" <b>{self.character.rarity}★</b> ")
        rarity_badge.setObjectName("rarityBadge")

        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeButton")
        close_btn.setFixedSize(22, 22)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(lambda: self.close_requested.emit(self))

        top_bar.addWidget(rarity_badge)
        top_bar.addStretch()
        top_bar.addWidget(close_btn)
        header_layout.addLayout(top_bar)

        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)
        icon_path = self.character.icon_path
        if os.path.exists(icon_path):
            img_label.setPixmap(QPixmap(icon_path).scaledToHeight(85, Qt.SmoothTransformation))
        else:
            img_label.setObjectName("cardImagePlaceholder")
            img_label.setText(f"[ {self.character.name} ]")
        header_layout.addWidget(img_label)
        return header_frame

    def _build_info(self, layout: QVBoxLayout):
        name_elem_box = QHBoxLayout()
        name_label = QLabel(f"<b>{self.character.name}</b>")
        name_label.setObjectName("cardName")
        elem_badge = QLabel(f" {self.character.element} ")
        elem_badge.setStyleSheet(element_badge_style(self.character.element))
        name_elem_box.addWidget(name_label)
        name_elem_box.addStretch()
        name_elem_box.addWidget(elem_badge)
        layout.addLayout(name_elem_box)

        self.char_level_spin = self._level_spin(self.saved_data.get("level", 90))
        sub_info_box = QHBoxLayout()
        sub_info = QLabel(f"{self.character.region} · {self.character.weapon_type}")
        sub_info.setObjectName("cardSubInfo")
        sub_info_box.addWidget(sub_info)
        sub_info_box.addStretch()
        sub_info_box.addWidget(self.char_level_spin)
        layout.addLayout(sub_info_box)

        self.constellation_row = ChoiceButtonRow(
            "C", range(0, 7), fmt=lambda c: f"C{c}", width=26,
            selected=self.saved_data.get("constellation", 0)
        )
        layout.addLayout(self.constellation_row)

    def _build_weapon(self, layout: QVBoxLayout):
        wpn_header_layout = QHBoxLayout()
        wpn_header_layout.setContentsMargins(0, 0, 0, 0)
        wpn_header_layout.setSpacing(4)
        wpn_header_layout.addWidget(section_title("Waffe"))

        btn_search_weapon = QPushButton("🔍")
        btn_search_weapon.setObjectName("iconButton")
        btn_search_weapon.setFixedSize(18, 18)
        btn_search_weapon.setCursor(Qt.PointingHandCursor)
        btn_search_weapon.setToolTip("Waffe suchen und filtern")
        btn_search_weapon.clicked.connect(self.open_weapon_search_dialog)
        wpn_header_layout.addWidget(btn_search_weapon)
        wpn_header_layout.addStretch()
        layout.addLayout(wpn_header_layout)

        self.wpn_input = ClickableLineEdit()
        self.wpn_input.setObjectName("weaponInput")
        self.wpn_input.setPlaceholderText("Waffe auswählen...")
        saved_wpn = self.saved_data.get("weapon", "")
        if saved_wpn:
            self.set_weapon(saved_wpn.replace("★", "").strip())
        else:
            matching = self.manager.get_weapons_by_type(self.character.weapon_type)
            if matching:
                self.set_weapon(matching[0].name)
        self.wpn_input.clicked.connect(self.open_weapon_search_dialog)

        self.wpn_level_spin = self._level_spin(self.saved_data.get("weapon_level", 90))

        wpn_box = QHBoxLayout()
        wpn_box.setSpacing(4)
        wpn_box.addWidget(self.wpn_input)
        wpn_box.addWidget(self.wpn_level_spin)
        layout.addLayout(wpn_box)

        self.refine_row = ChoiceButtonRow("V", range(1, 6), selected=self.saved_data.get("refinement", 1))
        layout.addLayout(self.refine_row)

    def _build_artifacts(self, layout: QVBoxLayout):
        art_header_layout = QHBoxLayout()
        art_header_layout.addWidget(section_title("Artefaktset"))
        self.toggle_stats_btn = QPushButton("+")
        self.toggle_stats_btn.setObjectName("toggleButton")
        self.toggle_stats_btn.setFixedSize(18, 18)
        self.toggle_stats_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_stats_btn.clicked.connect(self.toggle_detail_view)
        art_header_layout.addWidget(self.toggle_stats_btn)
        art_header_layout.addStretch()
        layout.addLayout(art_header_layout)

        self.art_combo = QComboBox()
        self.art_combo_2 = QComboBox()
        for combo in (self.art_combo, self.art_combo_2):
            combo.view().setMinimumWidth(300)

        # Platzhalter tragen den Wert "" und werden so nie als Set-Name gespeichert
        self.art_combo_2.addItem("— Zweites 2er-Set (optional) —", "")
        if self.manager.available_artifacts:
            for art in self.manager.available_artifacts:
                self.art_combo.addItem(art.name, art.name)
                self.art_combo_2.addItem(art.name, art.name)
        else:
            self.art_combo.addItem("Keine Artefakte geladen", "")

        if "artifact" in self.saved_data:
            select_value(self.art_combo, self.saved_data["artifact"])
        if "artifact_2" in self.saved_data:
            select_value(self.art_combo_2, self.saved_data["artifact_2"])

        for combo in (self.art_combo, self.art_combo_2):
            combo.currentIndexChanged.connect(lambda _, c=combo: self.update_artifact_tooltip(c))
            self.update_artifact_tooltip(combo)
            layout.addWidget(combo)

    def _build_talents(self, layout: QVBoxLayout):
        layout.addWidget(section_title("Talente (A / E / Q)"))
        talents = self.saved_data.get("talents", {})

        talent_layout = QHBoxLayout()
        talent_layout.setSpacing(4)
        self.talent_spins = {}
        for key, label in (("attack", "A:"), ("skill", "E:"), ("burst", "Q:")):
            spin = QSpinBox()
            spin.setRange(1, 13)
            spin.setValue(talents.get(key, DEFAULT_TALENTS[key]))
            spin.setFixedWidth(48)
            self.talent_spins[key] = spin
            talent_layout.addWidget(muted(label))
            talent_layout.addWidget(spin)
        layout.addLayout(talent_layout)

    @staticmethod
    def _level_spin(value: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(1, 90)
        spin.setValue(value)
        spin.setPrefix("Lvl ")
        spin.setFixedWidth(72)
        return spin

    # --- Aktionen ---

    def set_weapon(self, name: str):
        self.wpn_input.setText(name)
        self.wpn_input.setToolTip(name)
        self.wpn_input.setCursorPosition(0)

    def open_weapon_search_dialog(self):
        dialog = WeaponSearchDialog(self.manager.available_weapons, self.character.weapon_type, parent=self)
        if dialog.exec() == QDialog.Accepted and dialog.selected:
            self.set_weapon(dialog.selected.name)

    def update_artifact_tooltip(self, combo: QComboBox):
        art = self.manager.get_artifact_by_name(combo_value(combo))
        combo.setToolTip(self.format_artifact_tooltip(art) if art else "")

    @staticmethod
    def format_artifact_tooltip(art: ArtifactSet) -> str:
        parts = [f"<b>{art.name}</b>"]
        for label, bonus in (("1er", art.bonus_1pc), ("2er", art.bonus_2pc), ("4er", art.bonus_4pc)):
            if bonus:
                parts.append(f"<b>{label}-Bonus:</b> {bonus}")
        return "<br><br>".join(parts)

    def toggle_detail_view(self):
        self.is_detail_open = not self.is_detail_open
        self.toggle_stats_btn.setText("-" if self.is_detail_open else "+")
        self.toggle_detail_requested.emit(self, self.is_detail_open)

    def get_card_data(self) -> dict:
        # Ist das Detailpanel offen, werden dessen aktuelle Werte übernommen
        if self.artifact_panel is not None:
            try:
                self.saved_data["artifact_stats"] = self.artifact_panel.get_stats()
            except RuntimeError:
                # Panel-Widgets wurden bereits gelöscht -> gespeicherte Werte nicht überschreiben
                self.artifact_panel = None

        return {
            "name": self.character.name,
            "level": self.char_level_spin.value(),
            "constellation": self.constellation_row.value,
            "weapon": self.wpn_input.text(),
            "weapon_level": self.wpn_level_spin.value(),
            "refinement": self.refine_row.value,
            "artifact": combo_value(self.art_combo),
            "artifact_2": combo_value(self.art_combo_2),
            "artifact_stats": self.saved_data.get("artifact_stats", {}),
            "talents": {key: spin.value() for key, spin in self.talent_spins.items()},
        }


# --- Artefakt-Detailpanel ---

@dataclass
class ArtifactSlotWidgets:
    rarity: QComboBox
    level: QSpinBox
    main: QComboBox
    main_val: QLineEdit
    subs: list[tuple[QComboBox, QLineEdit]]


class ArtifactPanel(QFrame):
    """Panel mit Einzelwerten (Level, Haupt- und Substats) der fünf Artefakte einer Karte."""

    SLOTS = [
        ("Blume", ["LP (Fix)"]),
        ("Feder", ["ANG (Fix)"]),
        ("Sanduhr", ["ANG%", "LP%", "DEF%", "Elementarkunde", "Aufladerate"]),
        ("Kelch", [
            "Pyro-SCH-Bonus%", "Hydro-SCH-Bonus%", "Kryo-SCH-Bonus%", "Elektro-SCH-Bonus%",
            "Anemo-SCH-Bonus%", "Geo-SCH-Bonus%", "Dendro-SCH-Bonus%", "Physischer SCH-Bonus%",
            "ANG%", "LP%", "DEF%", "Elementarkunde",
        ]),
        ("Krone", ["KT%", "KSCH%", "ANG%", "LP%", "DEF%", "Heilungsbonus%", "Elementarkunde"]),
    ]
    SUBSTATS = ["KT%", "KSCH%", "ANG%", "ANG (Fix)", "LP%", "LP (Fix)",
                "DEF%", "DEF (Fix)", "Elementarkunde", "Aufladerate"]
    RARITIES = ["5★", "4★", "3★"]

    # Standard-Hauptwert des Kelchs je Element des Charakters
    GOBLET_BY_ELEMENT = {
        "Pyro": "Pyro-SCH-Bonus%", "Hydro": "Hydro-SCH-Bonus%", "Cryo": "Kryo-SCH-Bonus%",
        "Electro": "Elektro-SCH-Bonus%", "Anemo": "Anemo-SCH-Bonus%", "Geo": "Geo-SCH-Bonus%",
        "Dendro": "Dendro-SCH-Bonus%",
    }

    @classmethod
    def default_main_stat(cls, slot_name: str, main_stats: list[str], element: Optional[str]) -> str:
        """Standard-Hauptwert eines Slots: beim Kelch der Elementschaden des Charakters, sonst der erste Eintrag."""
        if slot_name == "Kelch":
            return cls.GOBLET_BY_ELEMENT.get(element, main_stats[0])
        return main_stats[0]

    @classmethod
    def default_stats(cls, element: Optional[str] = None) -> dict:
        """Die Werte, die ein unbearbeitetes Panel liefert (siehe set_stats({}) / get_stats())."""
        return {
            slot_name: {
                "rarity": cls.RARITIES[0], "level": 20,
                "main_stat": cls.default_main_stat(slot_name, main_stats, element), "main_value": "",
                "substats": [{"stat": "", "val": ""} for _ in range(4)],
            }
            for slot_name, main_stats in cls.SLOTS
        }

    def __init__(self, card: CharacterCardWidget, manager: GenshinManager, parent=None):
        super().__init__(parent)
        self.setObjectName("artifactPanel")
        element = card.character.element
        self.setStyleSheet(
            tint_style("QFrame#artifactPanel", element)
            + tint_style("QFrame#artifactSlot", element, darken=0.15, alpha=0.85, radius=8)
        )
        self.card = card
        self.manager = manager
        self.slots: dict[str, ArtifactSlotWidgets] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("<b>Artefakt-Einzelwerte, Level & Substats</b>")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(8)
        for idx, (slot_name, main_stats) in enumerate(self.SLOTS):
            grid.addWidget(self._build_slot(slot_name, main_stats), idx // 2, idx % 2)
        for row in range(3):
            grid.setRowStretch(row, 1)

        # Die Buttons stehen in der freien Zelle neben der Krone, unten bündig mit den Slot-Karten.
        # So füllen die Karten die ganze Höhe, und unten bleibt derselbe Abstand wie seitlich.
        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        for text, tooltip, handler, primary in (
            ("Zurücksetzen", "Leert alle eingegebenen Artefakt-Einzelwerte dieser Karte", self.reset, False),
            ("Neu laden", "Lädt die gespeicherten Artefaktwerte aus der SQLite-Datenbank neu", self.reload, False),
            ("Speichern", "Speichert das Build dieses Charakters zentral in der SQLite-Datenbank", self.save, True),
        ):
            btn = QPushButton(text)
            btn.setToolTip(tooltip)
            if primary:
                btn.setObjectName("primaryButton")
            btn.clicked.connect(handler)
            buttons.addWidget(btn)
        grid.addLayout(buttons, 2, 1, Qt.AlignBottom | Qt.AlignRight)
        layout.addLayout(grid, stretch=1)

        self.set_stats(card.saved_data.get("artifact_stats", {}))

    def _build_slot(self, slot_name: str, main_stats: list[str]) -> QFrame:
        box = QFrame()
        box.setObjectName("artifactSlot")
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(6, 6, 6, 6)
        box_layout.setSpacing(0)

        title = QLabel(slot_name)
        title.setObjectName("slotTitle")
        level = QSpinBox()
        level.setRange(0, 20)
        level.setPrefix("+")
        level.setFixedWidth(50)
        rarity = QComboBox()
        rarity.addItems(self.RARITIES)
        rarity.setFixedWidth(50)

        head = QHBoxLayout()
        head.addWidget(title)
        head.addStretch()
        head.addWidget(muted("Lvl:"))
        head.addWidget(level)
        head.addWidget(rarity)
        box_layout.addLayout(head)

        # Zusätzliche Höhe wird gleichmäßig auf die Abschnitte des Slots verteilt
        box_layout.addItem(QSpacerItem(0, 4, QSizePolicy.Minimum, QSizePolicy.Expanding))

        main = QComboBox()
        main.addItems(main_stats)
        main_val = self._value_input()
        main_box = QHBoxLayout()
        main_box.addWidget(main)
        main_box.addWidget(main_val)
        box_layout.addLayout(main_box)

        box_layout.addItem(QSpacerItem(0, 4, QSizePolicy.Minimum, QSizePolicy.Expanding))

        subs = []
        sub_grid = QGridLayout()
        sub_grid.setSpacing(3)
        for i in range(4):
            cb = QComboBox()
            cb.addItem("— Keiner —", "")
            for opt in self.SUBSTATS:
                cb.addItem(opt, opt)
            val = self._value_input()
            sub_box = QHBoxLayout()
            sub_box.setSpacing(2)
            sub_box.addWidget(cb)
            sub_box.addWidget(val)
            sub_grid.addLayout(sub_box, i // 2, i % 2)
            subs.append((cb, val))
        box_layout.addLayout(sub_grid)

        self.slots[slot_name] = ArtifactSlotWidgets(rarity, level, main, main_val, subs)
        return box

    @staticmethod
    def _value_input() -> QLineEdit:
        edit = QLineEdit()
        edit.setPlaceholderText("Wert")
        edit.setFixedWidth(50)
        return edit

    # --- Werte lesen / setzen ---

    def set_stats(self, stats: dict):
        """Überträgt gespeicherte Werte in die Felder; fehlende Werte werden auf Standard gesetzt."""
        for slot_name, w in self.slots.items():
            saved = stats.get(slot_name)
            if not isinstance(saved, dict):
                saved = {}
            select_value(w.rarity, saved.get("rarity", "5★"))
            w.level.setValue(saved.get("level", 20))
            main_stats = dict(self.SLOTS)[slot_name]
            select_value(w.main, saved.get("main_stat") or
                         self.default_main_stat(slot_name, main_stats, self.card.character.element))
            w.main_val.setText(str(saved.get("main_value", "")))

            subs = saved.get("substats", [])
            for i, (cb, val) in enumerate(w.subs):
                sub = subs[i] if i < len(subs) and isinstance(subs[i], dict) else {}
                select_value(cb, sub.get("stat", ""))
                val.setText(str(sub.get("val", "")))

    def get_stats(self) -> dict:
        return {
            slot_name: {
                "rarity": w.rarity.currentText(),
                "level": w.level.value(),
                "main_stat": w.main.currentText(),
                "main_value": w.main_val.text(),
                "substats": [{"stat": combo_value(cb), "val": val.text()} for cb, val in w.subs],
            }
            for slot_name, w in self.slots.items()
        }

    # --- Button-Aktionen ---

    def reset(self):
        self.set_stats({})

    def reload(self):
        try:
            builds = self.manager.load_user_characters()
        except DatabaseError as e:
            show_db_error(self, e)
            return
        self.set_stats(builds.get(self.card.character.name, {}).get("artifact_stats", {}))

    def save(self):
        name = self.card.character.name
        try:
            self.manager.save_user_character(name, self.card.get_card_data())
        except DatabaseError as e:
            show_db_error(self, e)
            return
        QMessageBox.information(self, "Gespeichert",
                                f"Das Build für '{name}' wurde zentral in der SQLite-Datenbank gespeichert!")
