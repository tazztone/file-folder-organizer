import sys
import os
from PySide6.QtWidgets import QApplication
from pro_file_organizer.ui.main_window import OrganizerApp

app = QApplication(sys.argv)
window = OrganizerApp()
window.resize(1100, 750)
window.show()
pixmap = window.grab()
pixmap.save("screenshot.png")
