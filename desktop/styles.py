"""Zentrales Qt-Stylesheet der Anwendung.

Wird einmal per QApplication.setStyleSheet() gesetzt. Varianten werden über
objectName (#name) oder dynamische Properties ([selected="true"]) gesteuert.
"""

# Farbpalette
BG_WINDOW = "#0d0b14"
BG_PANEL = "#1a1825"
BG_INPUT = "#12101b"
BG_HOVER = "#252136"
BORDER = "#332d47"
BORDER_SOFT = "#2d293e"
ACCENT = "#5bc0be"
ACCENT_HOVER = "#4ab0ad"
GOLD = "#d89f53"
DANGER = "#df4a28"
TEXT = "#ffffff"
TEXT_SOFT = "#e1e1e6"
TEXT_MUTED = "#8a889e"

ELEMENT_COLORS = {
    "Dendro": "#26bb3a", "Anemo": "#23c197", "Pyro": "#df4a28",
    "Hydro": "#2393c1", "Electro": "#9643db", "Cryo": "#62c8db", "Geo": "#cba128",
}

APP_QSS = f"""
/* ---------- Grundelemente ---------- */
QMainWindow {{ background-color: {BG_WINDOW}; }}
QDialog {{ background-color: {BG_PANEL}; color: {TEXT}; }}
QDialog QLabel {{ color: {TEXT}; font-size: 12px; }}

QToolTip {{
    background-color: {BG_INPUT}; color: {TEXT};
    border: 1px solid {ACCENT}; border-radius: 6px;
    padding: 6px; font-size: 11px;
}}

QLineEdit {{
    background-color: {BG_INPUT}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: 6px;
    padding: 4px 6px; font-size: 11px;
}}

QComboBox {{
    background-color: {BG_INPUT}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: 6px;
    padding: 4px 18px 4px 6px; font-size: 11px;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_PANEL}; color: {TEXT};
    selection-background-color: {ACCENT}; selection-color: {BG_INPUT};
    border: 1px solid {BORDER}; outline: none;
}}

QSpinBox {{
    background-color: {BG_INPUT}; color: {ACCENT};
    border: 1px solid {BORDER}; border-radius: 4px;
    padding-left: 2px; padding-right: 14px;
    font-size: 11px; font-weight: bold;
}}
QSpinBox::up-button, QSpinBox::down-button {{ width: 12px; }}

QPushButton {{
    background-color: {ACCENT}; color: {BG_INPUT}; font-weight: bold;
    border: none; border-radius: 6px; padding: 6px 12px; font-size: 12px;
}}
QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}
QPushButton#dangerButton {{ background-color: {DANGER}; color: {TEXT}; }}

/* ---------- Suchdialoge ---------- */
QDialog QLineEdit, QDialog QComboBox {{ padding: 5px; font-size: 12px; }}
QDialog QPushButton {{ border-radius: 4px; }}
QLabel#statusLabel {{ color: {TEXT_MUTED}; }}

QTableWidget {{
    background-color: {BG_INPUT}; color: {TEXT};
    gridline-color: {BG_HOVER}; border: 1px solid {BORDER};
    border-radius: 6px; font-size: 12px;
}}
QTableWidget::item {{ padding: 4px; }}
QTableWidget::item:selected {{ background-color: {BORDER}; color: {ACCENT}; }}
QHeaderView::section {{
    background-color: {BG_PANEL}; color: {GOLD};
    padding: 4px; border: none; font-weight: bold;
}}

/* ---------- Leerer Slot ---------- */
AddCharacterSlotWidget {{
    background-color: rgba(26, 24, 37, 0.4);
    border: 2px dashed {BORDER}; border-radius: 12px;
}}
AddCharacterSlotWidget:hover {{
    background-color: rgba(43, 39, 61, 0.6); border-color: {ACCENT};
}}
QLabel#addSlotPlus {{ font-size: 48px; color: {ACCENT}; }}
QLabel#addSlotText {{ font-size: 13px; color: {TEXT_MUTED}; font-weight: bold; }}

/* ---------- Charakterkarte ---------- */
CharacterCardWidget {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER_SOFT}; border-radius: 12px;
}}
CharacterCardWidget QLabel {{ color: {TEXT_SOFT}; }}
CharacterCardWidget QComboBox {{ color: #d1d1d6; padding: 4px 24px 4px 8px; }}
CharacterCardWidget QComboBox QAbstractItemView {{
    background-color: {BG_INPUT};
    selection-background-color: {BG_HOVER}; selection-color: {ACCENT};
    border: 1px solid {ACCENT}; border-radius: 6px; padding: 4px;
}}

QFrame#cardHeader {{
    border: none; border-top-left-radius: 12px; border-top-right-radius: 12px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #593d7a, stop:1 #29243b);
}}
QFrame#cardHeader[rarity="5"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8a602a, stop:1 #2d241d);
}}
QFrame#cardHeader QLabel {{ background: transparent; border: none; color: {TEXT}; }}
QLabel#cardImagePlaceholder {{ color: rgba(255,255,255,0.8); font-size: 12px; font-weight: bold; }}
QFrame#cardHeader QLabel#rarityBadge {{
    background: rgba(0,0,0,0.5); border-radius: 4px; padding: 2px 4px; font-size: 10px;
}}

QPushButton#closeButton {{
    background-color: rgba(0, 0, 0, 0.6); color: {TEXT};
    border-radius: 11px; font-size: 12px; padding: 0px;
}}
QPushButton#closeButton:hover {{ background-color: {DANGER}; }}

QLabel#cardName {{ font-size: 15px; color: {TEXT}; }}
QLabel#cardSubInfo {{ font-size: 11px; color: #7a788e; }}
QLabel#sectionTitle {{ color: {GOLD}; font-size: 11px; font-weight: bold; margin-top: 4px; }}
QLabel#choiceLabel {{ color: {GOLD}; font-size: 11px; font-weight: bold; margin-right: 2px; }}

QPushButton#iconButton {{
    background-color: {BG_INPUT}; color: {ACCENT};
    border: 1px solid {BORDER}; border-radius: 4px; font-size: 10px; padding: 0px;
}}
QPushButton#iconButton:hover {{ background-color: {BG_HOVER}; border-color: {ACCENT}; }}

QPushButton#toggleButton {{
    background-color: {BORDER_SOFT}; color: {ACCENT};
    border: 1px solid {BORDER}; border-radius: 9px; font-size: 11px; padding: 0px;
}}
QPushButton#toggleButton:hover {{ background-color: {ACCENT}; color: {BG_INPUT}; }}

QLineEdit#weaponInput {{ color: #d1d1d6; padding: 4px 8px; }}
QLineEdit#weaponInput:hover {{ border-color: {ACCENT}; color: {TEXT}; }}

/* Auswahl-Buttons für Sternbild (C0–C6) und Veredelung (1–5) */
QPushButton#choiceButton {{
    background-color: {BG_INPUT}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: 4px;
    font-size: 10px; padding: 0px;
}}
QPushButton#choiceButton:hover {{ background-color: {BG_HOVER}; color: {ACCENT}; border-color: {ACCENT}; }}
QPushButton#choiceButton[selected="true"] {{
    background-color: {BORDER_SOFT}; color: {GOLD}; border-color: {GOLD};
}}

/* ---------- Artefakt-Detailpanel ---------- */
QFrame#artifactPanel {{
    background-color: {BG_INPUT}; border: 1px solid {BORDER}; border-radius: 12px;
}}
QFrame#artifactPanel QLabel {{ color: {GOLD}; font-size: 11px; }}
QFrame#artifactPanel QLabel#panelTitle {{ color: {ACCENT}; font-size: 14px; font-weight: bold; }}
QFrame#artifactPanel QPushButton {{
    background-color: {BG_HOVER}; color: {ACCENT};
    border: 1px solid {BORDER}; font-size: 11px;
}}
QFrame#artifactPanel QPushButton:hover {{ background-color: {BORDER}; border-color: {ACCENT}; }}
QFrame#artifactPanel QPushButton#primaryButton {{
    background-color: {ACCENT}; color: {BG_INPUT}; border: none;
}}
QFrame#artifactPanel QPushButton#primaryButton:hover {{ background-color: {ACCENT_HOVER}; }}

QFrame#artifactSlot {{
    background-color: {BG_PANEL}; border: 1px solid {BORDER_SOFT}; border-radius: 8px;
}}
QFrame#artifactSlot QLabel#slotTitle {{ color: {TEXT_SOFT}; font-weight: bold; }}
QFrame#artifactSlot QComboBox, QFrame#artifactSlot QLineEdit {{ padding: 4px; }}
"""


def element_badge_style(element: str) -> str:
    """Stil für das farbige Element-Abzeichen (Farbe hängt vom Element ab)."""
    color = ELEMENT_COLORS.get(element, ACCENT)
    return (
        f"background-color: rgba(0,0,0,0.3); color: {color};"
        f"border: 1px solid {color}; border-radius: 10px;"
        "padding: 2px 8px; font-size: 11px; font-weight: bold;"
    )


def set_selected(widget, selected: bool):
    """Setzt die Property `selected` und aktualisiert den Stil des Widgets."""
    widget.setProperty("selected", selected)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
