import importlib
import sys
import unittest
from unittest.mock import MagicMock, patch

from tests.ui_test_utils import get_pyside_mocks

# Apply standardized mocks
mock_qtwidgets, mock_qtcore, mock_qtgui = get_pyside_mocks()
sys.modules["PySide6.QtWidgets"] = mock_qtwidgets
sys.modules["PySide6.QtCore"] = mock_qtcore
sys.modules["PySide6.QtGui"] = mock_qtgui

# Mock out heavy imports in core to avoid environment issues in CI
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()

import pro_file_organizer.ui.main_window

importlib.reload(pro_file_organizer.ui.main_window)
from pro_file_organizer.ui.main_window import OrganizerApp


class TestStartupRegression(unittest.TestCase):
    @patch("pro_file_organizer.ui.main_window.FileOrganizer")
    @patch("pro_file_organizer.ui.main_window.MultimodalFileOrganizer")
    def test_app_initialization_order(self, mock_ml, mock_org):
        # Configure the mocked organizer
        mock_org_instance = mock_org.return_value
        mock_org_instance.get_theme_mode.return_value = "System"

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
