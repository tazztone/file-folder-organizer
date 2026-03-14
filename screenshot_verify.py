import sys

from PySide6.QtWidgets import QApplication

from pro_file_organizer.ui.main_window import OrganizerApp


def capture():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    window = OrganizerApp()
    window.resize(1100, 750)
    # Force light theme for verification
    window.change_appearance_mode_event("Light")
    window.show()

    # Process events to ensure UI is rendered
    app.processEvents()

    pixmap = window.grab()
    pixmap.save("verification_light.png")
    print("Screenshot saved to verification_light.png")

    # Also dark theme
    window.change_appearance_mode_event("Dark")
    app.processEvents()
    pixmap = window.grab()
    pixmap.save("verification_dark.png")
    print("Screenshot saved to verification_dark.png")


if __name__ == "__main__":
    capture()
