import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from pro_file_organizer.ui.ui_utils import ToolTip

class TestUIUtils(unittest.TestCase):
    def setUp(self):
        self.mock_widget = MagicMock()
        # Mocking for show_tip's geometry calculation
        self.mock_widget.winfo_rootx.return_value = 100
        self.mock_widget.winfo_rooty.return_value = 100
        self.mock_widget.winfo_height.return_value = 50
        self.tooltip = ToolTip(self.mock_widget, "Test Tooltip")

    def test_init(self):
        self.assertEqual(self.tooltip.text, "Test Tooltip")
        self.mock_widget.bind.assert_called()

    @patch('pro_file_organizer.ui.ui_utils.ctk')
    @patch('pro_file_organizer.ui.ui_utils.tk.Toplevel')
    def test_show_tip(self, mock_toplevel, mock_ctk):
        mock_tw = MagicMock()
        mock_toplevel.return_value = mock_tw
        
        self.tooltip.show_tip()
        self.assertIsNotNone(self.tooltip.tip_window)
        mock_toplevel.assert_called()

    def test_hide_tip(self):
        mock_tw = MagicMock()
        self.tooltip.tip_window = mock_tw
        self.tooltip.hide_tip()
        self.assertIsNone(self.tooltip.tip_window)
        mock_tw.destroy.assert_called()

if __name__ == '__main__':
    unittest.main()
