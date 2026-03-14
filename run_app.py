import argparse
import sys

from PySide6.QtWidgets import QApplication

from pro_file_organizer.ui.main_window import OrganizerApp

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pro File Organizer")
    parser.add_argument("--version", action="version", version="Pro File Organizer 0.1.0")
    args, unknown = parser.parse_known_args()

    app = QApplication(sys.argv)
    window = OrganizerApp()
    window.show()
    sys.exit(app.exec())
