from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QStackedWidget, QMessageBox, QDialog
)

from manager import GenshinManager, DatabaseError
from dialogs import CharacterSearchDialog
from widgets import CharacterCardWidget, AddCharacterSlotWidget, ArtifactPanel, normalize_build, show_db_error

MAX_TEAM_SIZE = 4
CARD_MIN_WIDTH = 230
CARD_MAX_WIDTH = 280
CARD_DETAIL_WIDTH = 250
NEW_TEAM_NAME = "Neues Team"


class MainWindow(QMainWindow):
    def __init__(self, manager: Optional[GenshinManager] = None):
        super().__init__()
        self.setWindowTitle("Genshin Team-Slots Manager")
        self.setMinimumSize(1080, 640)
        self.resize(1080, 640)

        self.manager = manager or GenshinManager()
        self.current_team_cards: list[CharacterCardWidget] = []
        # Name des zuletzt geladenen/gespeicherten Teams (für das Erkennen von Umbenennungen)
        self.loaded_team_name: Optional[str] = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.addLayout(self._build_header())

        # Seite 1: Teamübersicht, Seite 2: Karte + Artefakt-Detailpanel
        self.stack = QStackedWidget()

        self.team_overview_widget = QWidget()
        self.cards_layout = QHBoxLayout(self.team_overview_widget)
        self.cards_layout.setContentsMargins(15, 10, 15, 10)
        self.cards_layout.setSpacing(12)

        self.detail_widget = QWidget()
        self.detail_layout = QHBoxLayout(self.detail_widget)
        self.detail_layout.setContentsMargins(15, 10, 15, 10)
        self.detail_layout.setSpacing(15)

        self.stack.addWidget(self.team_overview_widget)
        self.stack.addWidget(self.detail_widget)
        main_layout.addWidget(self.stack)

        self.update_teams_dropdown()

        if self.manager.load_errors:
            QMessageBox.warning(
                self, "Datenbankfehler",
                "Beim Laden der Datenbank sind Fehler aufgetreten:\n\n" + "\n".join(self.manager.load_errors)
            )

        if self.manager.saved_teams:
            first_team = next(iter(self.manager.saved_teams))
            self.teams_combo.setCurrentText(first_team)
        else:
            self.render_team_cards([])

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(10)

        header.addWidget(QLabel("<b style='color: #e1e1e6;'>Team Name:</b>"))
        self.team_name_input = QLineEdit(NEW_TEAM_NAME)
        self.team_name_input.setFixedWidth(160)
        header.addWidget(self.team_name_input)

        new_btn = QPushButton("Neues Team")
        new_btn.clicked.connect(self.new_team)
        header.addWidget(new_btn)

        save_btn = QPushButton("Team Speichern")
        save_btn.clicked.connect(self.save_current_team)
        header.addWidget(save_btn)

        header.addStretch()

        header.addWidget(QLabel("<b style='color: #e1e1e6;'>Gespeicherte Teams:</b>"))
        self.teams_combo = QComboBox()
        self.teams_combo.setFixedWidth(180)
        self.teams_combo.currentIndexChanged.connect(self.on_team_selected)
        header.addWidget(self.teams_combo)

        delete_btn = QPushButton("Löschen")
        delete_btn.setObjectName("dangerButton")
        delete_btn.clicked.connect(self.delete_current_team)
        header.addWidget(delete_btn)
        return header

    # --- Hilfsmethoden ---

    def load_builds(self) -> dict:
        """Lädt die Charakter-Builds; bei einem Fehler wird dieser angezeigt und {} zurückgegeben."""
        try:
            return self.manager.load_user_characters()
        except DatabaseError as e:
            show_db_error(self, e)
            return {}

    def has_unsaved_changes(self) -> bool:
        """Prüft, ob die Ansicht vom gespeicherten Stand (Teammitglieder und Builds) abweicht."""
        if not self.current_team_cards:
            return False

        saved_members = self.manager.saved_teams.get(self.loaded_team_name)
        if saved_members is None:
            return True  # Team wurde noch nie gespeichert

        saved_names = [m.get("name", "") if isinstance(m, dict) else m for m in saved_members]
        if [c.character.name for c in self.current_team_cards] != saved_names:
            return True

        try:
            saved_builds = self.manager.load_user_characters()
        except DatabaseError:
            return True  # Im Zweifel lieber nachfragen

        for card in self.current_team_cards:
            saved = saved_builds.get(card.character.name)
            if saved is None or normalize_build(card.get_card_data()) != normalize_build(saved):
                return True
        return False

    def confirm_discard(self, title: str, question: str) -> bool:
        """Fragt nach, wenn das aktuelle Team ungespeicherte Änderungen hat. True = weitermachen."""
        if not self.has_unsaved_changes():
            return True
        answer = QMessageBox.question(
            self, title,
            f"Das aktuelle Team hat nicht gespeicherte Änderungen, die verloren gehen.\n\n{question}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        return answer == QMessageBox.Yes

    def current_team_data(self) -> list[dict]:
        return [{"character": c.character, "saved": c.get_card_data()} for c in self.current_team_cards]

    def clear_detail_layout(self, keep=None):
        """Leert die Detailansicht. Das Widget `keep` wird nur herausgenommen, nicht gelöscht."""
        while self.detail_layout.count():
            widget = self.detail_layout.takeAt(0).widget()
            if widget and widget is not keep:
                widget.deleteLater()

    # --- Karten ---

    def render_team_cards(self, team_data: list):
        self.stack.setCurrentWidget(self.team_overview_widget)
        # Eine evtl. noch in der Detailansicht liegende Karte samt Panel entfernen
        self.clear_detail_layout()

        while self.cards_layout.count():
            widget = self.cards_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        self.current_team_cards = []
        for item in team_data:
            card = CharacterCardWidget(item["character"], self.manager, saved_data=item.get("saved", {}))
            card.setMinimumWidth(CARD_MIN_WIDTH)
            card.setMaximumWidth(CARD_MAX_WIDTH)
            card.close_requested.connect(self.remove_character)
            card.toggle_detail_requested.connect(self.handle_toggle_detail)
            self.cards_layout.addWidget(card, stretch=1)
            self.current_team_cards.append(card)

        if len(self.current_team_cards) < MAX_TEAM_SIZE:
            add_slot = AddCharacterSlotWidget()
            add_slot.setMinimumWidth(CARD_MIN_WIDTH)
            add_slot.setMaximumWidth(CARD_MAX_WIDTH)
            add_slot.clicked.connect(self.open_add_character_dialog)
            self.cards_layout.addWidget(add_slot, stretch=1)

    def handle_toggle_detail(self, card: CharacterCardWidget, is_opening: bool):
        if is_opening:
            self.cards_layout.removeWidget(card)
            self.clear_detail_layout()

            card.setFixedWidth(CARD_DETAIL_WIDTH)
            card.artifact_panel = ArtifactPanel(card, self.manager)
            self.detail_layout.addWidget(card, stretch=0)
            self.detail_layout.addWidget(card.artifact_panel, stretch=1)
            self.stack.setCurrentWidget(self.detail_widget)
            return

        # Schließen: Eingaben sichern, bevor das Panel entfernt wird
        card.get_card_data()
        card.artifact_panel = None
        self.clear_detail_layout(keep=card)

        card.setMinimumWidth(CARD_MIN_WIDTH)
        card.setMaximumWidth(CARD_MAX_WIDTH)
        self.cards_layout.insertWidget(self.current_team_cards.index(card), card, stretch=1)
        card.is_detail_open = False
        card.toggle_stats_btn.setText("+")
        self.stack.setCurrentWidget(self.team_overview_widget)

    def remove_character(self, card: CharacterCardWidget):
        if card in self.current_team_cards:
            self.current_team_cards.remove(card)
            self.render_team_cards(self.current_team_data())

    def open_add_character_dialog(self):
        if len(self.current_team_cards) >= MAX_TEAM_SIZE:
            QMessageBox.warning(self, "Team voll", f"Ein Team kann maximal {MAX_TEAM_SIZE} Charaktere enthalten.")
            return

        # Charaktere, die schon im Team sind, werden nicht angeboten
        in_team = {card.character.name for card in self.current_team_cards}
        available = [c for c in self.manager.available_characters if c.name not in in_team]
        dialog = CharacterSearchDialog(available, self)
        if dialog.exec() == QDialog.Accepted and dialog.selected:
            selected_char = dialog.selected
            team_data = self.current_team_data()
            preset = self.load_builds().get(selected_char.name, {})
            team_data.append({"character": selected_char, "saved": preset})
            self.render_team_cards(team_data)

    # --- Teams ---

    def save_current_team(self):
        team_name = self.team_name_input.text().strip()
        if not team_name:
            QMessageBox.warning(self, "Fehler", "Bitte gib einen Namen für das Team ein.")
            return

        old_name = self.loaded_team_name
        is_other_team = old_name is not None and old_name != team_name and old_name in self.manager.saved_teams

        if team_name in self.manager.saved_teams and team_name != old_name:
            answer = QMessageBox.question(
                self, "Team existiert bereits",
                f"Es gibt bereits ein Team '{team_name}'. Soll es überschrieben werden?"
            )
            if answer != QMessageBox.Yes:
                return

        rename = False
        if is_other_team:
            choice = self.ask_rename(old_name, team_name)
            if choice is None:
                return
            rename = choice == "rename"

        team_list = [card.get_card_data() for card in self.current_team_cards]
        try:
            for card_data in team_list:
                self.manager.save_user_character(card_data["name"], card_data)
            if rename:
                self.manager.rename_team(old_name, team_name)
            self.manager.saved_teams[team_name] = team_list
            self.manager.save_teams()
        except DatabaseError as e:
            show_db_error(self, e)
            self.update_teams_dropdown()
            return

        self.loaded_team_name = team_name
        QMessageBox.information(self, "Gespeichert", f"Team '{team_name}' und Charakter-Builds wurden in SQLite gespeichert!")
        self.update_teams_dropdown(select_name=team_name)

    def ask_rename(self, old_name: str, new_name: str) -> Optional[str]:
        """Fragt, ob das geladene Team umbenannt oder als neues Team gespeichert werden soll.

        Rückgabe: "rename", "new" oder None (abgebrochen).
        """
        box = QMessageBox(self)
        box.setWindowTitle("Teamname geändert")
        box.setText(f"Der Name wurde von '{old_name}' zu '{new_name}' geändert.")
        box.setInformativeText("Soll das Team umbenannt oder als neues Team gespeichert werden?")
        btn_rename = box.addButton("Umbenennen", QMessageBox.AcceptRole)
        btn_new = box.addButton("Als neues Team", QMessageBox.AcceptRole)
        box.addButton("Abbrechen", QMessageBox.RejectRole)
        box.setDefaultButton(btn_rename)
        box.exec()
        clicked = box.clickedButton()
        if clicked is btn_rename:
            return "rename"
        if clicked is btn_new:
            return "new"
        return None

    def new_team(self):
        """Verwirft das aktuelle Team in der Ansicht und beginnt mit einem leeren Team."""
        if not self.confirm_discard("Neues Team", "Trotzdem ein neues Team beginnen?"):
            return

        # Einen noch nicht vergebenen Namen vorschlagen: "Neues Team", "Neues Team 2", ...
        name, n = NEW_TEAM_NAME, 2
        while name in self.manager.saved_teams:
            name = f"{NEW_TEAM_NAME} {n}"
            n += 1

        self.loaded_team_name = None
        self.team_name_input.setText(name)
        self.update_teams_dropdown()  # Auswahl zurück auf "— Team wählen —"
        self.render_team_cards([])

    def update_teams_dropdown(self, select_name: str = None):
        self.teams_combo.blockSignals(True)
        self.teams_combo.clear()
        self.teams_combo.addItem("— Team wählen —")
        for name in self.manager.saved_teams:
            self.teams_combo.addItem(name)

        if select_name and select_name in self.manager.saved_teams:
            idx = self.teams_combo.findText(select_name)
            if idx >= 0:
                self.teams_combo.setCurrentIndex(idx)
        self.teams_combo.blockSignals(False)

    def on_team_selected(self, index: int):
        team_name = self.teams_combo.currentText()
        if team_name not in self.manager.saved_teams:
            return

        if not self.confirm_discard("Team wechseln", f"Trotzdem zu '{team_name}' wechseln?"):
            # Auswahl auf das bisherige Team zurücksetzen, ohne erneut on_team_selected auszulösen
            self.teams_combo.blockSignals(True)
            previous = self.teams_combo.findText(self.loaded_team_name or "")
            self.teams_combo.setCurrentIndex(max(previous, 0))
            self.teams_combo.blockSignals(False)
            return

        self.loaded_team_name = team_name
        self.team_name_input.setText(team_name)
        user_builds = self.load_builds()

        team_data = []
        for entry in self.manager.saved_teams[team_name]:
            char_name = entry.get("name", "") if isinstance(entry, dict) else entry
            team_data.append({
                "character": self.manager.get_character_by_name(char_name),
                "saved": user_builds.get(char_name, {"name": char_name}),
            })
        self.render_team_cards(team_data)

    def delete_current_team(self):
        team_name = self.teams_combo.currentText()
        if team_name not in self.manager.saved_teams:
            return

        del self.manager.saved_teams[team_name]
        try:
            self.manager.save_teams()
        except DatabaseError as e:
            show_db_error(self, e)
            self.update_teams_dropdown(select_name=team_name)
            return

        self.loaded_team_name = None
        QMessageBox.information(self, "Gelöscht", f"Team '{team_name}' wurde aus SQLite gelöscht.")
        self.update_teams_dropdown()
        self.render_team_cards([])
