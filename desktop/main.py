"""Startpunkt der Anwendung: python main.py"""
import sys

from PySide6.QtWidgets import QApplication

from main_window import MainWindow
from styles import APP_QSS


def main():
    app = QApplication(sys.argv)
    # Eigene Fensterklasse (Wayland app_id), damit generische KWin-Regeln für "python" nicht greifen
    app.setApplicationName("genshin-team-manager")
    app.setDesktopFileName("genshin-team-manager")
    app.setStyleSheet(APP_QSS)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
