import importlib
import sys
import unittest
from unittest.mock import MagicMock, patch

# Standard Setup for UI Tests
from tests.ui_test_utils import get_ui_mocks

mock_ctk, mock_dnd = get_ui_mocks()

# Set up the mocks in sys.modules
sys.modules["customtkinter"] = mock_ctk
sys.modules["tkinterdnd2"] = mock_dnd

# Mock out heavy imports in core to avoid environment issues in CI
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()

import pro_file_organizer.ui.main_window

importlib.reload(pro_file_organizer.ui.main_window)
from pro_file_organizer.ui.main_window import OrganizerApp


class TestStartupRegression(unittest.TestCase):
    """
    Test specifically designed to catch the AttributeError: '_tkinter.tkapp' object has no attribute 'lbl_stats_total'
    at startup. This test uses a real MainWindowController with a mocked OrganizerApp UI.
    """

    @patch("pro_file_organizer.ui.main_window.FileOrganizer")
    @patch("pro_file_organizer.ui.main_window.MultimodalFileOrganizer")
    @patch("pro_file_organizer.ui.main_window.messagebox")
    @patch("pro_file_organizer.ui.main_window.filedialog")
    def test_app_initialization_order(self, mock_fd, mock_msg, mock_ml, mock_org):
        # Configure the mocked organizer to return some default stats
        mock_org_instance = mock_org.return_value
        mock_org_instance.get_theme_mode.return_value = "System"

        # This will trigger the full __init__ sequence including controller instantiation
        # If the order is wrong, this will raise AttributeError
        try:
            app = OrganizerApp()
            self.assertIsNotNone(app.controller)
            self.assertIsNotNone(app.lbl_stats_total)
        except AttributeError as e:
            self.fail(f"OrganizerApp failed to initialize due to AttributeError: {e}")
        except Exception as e:
            self.fail(f"OrganizerApp failed to initialize due to unexpected error: {e}")


if __name__ == "__main__":
    unittest.main()
