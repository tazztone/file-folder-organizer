import unittest
from unittest.mock import MagicMock, patch
import sys
import tkinter as tk

# Robust Base Classes for UI Mocks - avoiding metaclass conflicts
class MockDnD:
    def drop_target_register(self, *args): pass
    def dnd_bind(self, *args): pass

class MockCTkFrame(tk.Frame):
    def __init__(self, master=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
    def cget(self, *args): return MagicMock()
    def configure(self, *args, **kwargs): pass
    def update(self): pass
    def update_idletasks(self): pass
    def winfo_children(self): return []

class MockCTk(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def withdraw(self): pass
    def deiconify(self): pass
    def title(self, *args): pass
    def geometry(self, *args): pass
    def grid_columnconfigure(self, *args, **kwargs): pass
    def grid_rowconfigure(self, *args, **kwargs): pass

mock_ctk = MagicMock()
# Use the classes directly
mock_ctk.CTk = MockCTk
mock_ctk.CTkFrame = MockCTkFrame
mock_ctk.CTkLabel = MagicMock
mock_ctk.CTkButton = MagicMock
mock_ctk.CTkSwitch = MagicMock
mock_ctk.CTkOptionMenu = MagicMock
mock_ctk.CTkCheckBox = MagicMock
mock_ctk.CTkSlider = MagicMock
mock_ctk.CTkProgressBar = MagicMock
mock_ctk.CTkScrollableFrame = MockCTkFrame
mock_ctk.BooleanVar = tk.BooleanVar
mock_ctk.set_appearance_mode = MagicMock()
mock_ctk.get_appearance_mode = MagicMock(return_value="Light")
mock_ctk.set_default_color_theme = MagicMock()
mock_ctk.CTkFont = MagicMock()
sys.modules['customtkinter'] = mock_ctk

mock_dnd = MagicMock()
mock_dnd.TkinterDnD = MagicMock()
# IMPORTANT: DnDWrapper must be a CLASS to avoid metaclass conflict with MockCTk (which is a class)
class DnDWrapperMock:
    def drop_target_register(self, *args): pass
    def dnd_bind(self, *args): pass
mock_dnd.DnDWrapper = DnDWrapperMock
sys.modules['tkinterdnd2'] = mock_dnd

# Patch the module before import if it hasn't been imported yet
from pro_file_organizer.ui.main_window import OrganizerApp

class TestMainWindow(unittest.TestCase):
    @patch('pro_file_organizer.ui.main_window.FileOrganizer')
    @patch('pro_file_organizer.core.ml_organizer.MultimodalFileOrganizer')
    @patch('pro_file_organizer.ui.main_window.os.path.exists', return_value=False)
    def setUp(self, mock_exists, mock_ml, mock_organizer):
        self.mock_organizer = mock_organizer.return_value
        self.mock_ml = mock_ml.return_value
        # Mock view methods that are called during init
        with patch('pro_file_organizer.ui.main_window.OrganizerApp._setup_ui'):
            self.app = OrganizerApp()

    def test_init(self):
        self.assertIsNotNone(self.app.controller)
        self.assertEqual(self.app.organizer, self.mock_organizer)

    def test_view_interface_calls(self):
        self.app.lbl_status = MagicMock()
        self.app.show_status("Test Status")
        self.app.lbl_status.configure.assert_called()

if __name__ == '__main__':
    unittest.main()
