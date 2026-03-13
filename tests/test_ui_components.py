import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk

# Mock ctk before importing components
with patch('customtkinter.CTkFrame', MagicMock):
    from pro_file_organizer.ui.components.ui_components import FileCard, ModelDownloadModal

class TestUIComponents(unittest.TestCase):
    def setUp(self):
        self.mock_parent = MagicMock()
        # Mock some basic widget methods that might be called
        self.mock_parent.winfo_toplevel.return_value = MagicMock()

    @patch('pro_file_organizer.ui.components.ui_components.ctk')
    def test_file_card_init(self, mock_ctk):
        # Mock the widgets created inside FileCard
        mock_ctk.CTkFrame.return_value = MagicMock()
        mock_ctk.CTkLabel.return_value = MagicMock()
        
        data = {"file": "test.txt", "category": "Documents", "status": "Moved", "icon": "📄"}
        # FileCard requires data['file'], data['category'], etc.
        card = FileCard(self.mock_parent, data)
        # Verify it initialized components
        mock_ctk.CTkFrame.assert_called()
        self.assertEqual(card.file_data, data)

    @patch('pro_file_organizer.ui.components.ui_components.ctk')
    def test_model_download_modal_init(self, mock_ctk):
        on_complete = MagicMock()
        mock_ctk.CTkToplevel.return_value = MagicMock()
        
        modal = ModelDownloadModal(self.mock_parent, on_complete)
        self.assertEqual(modal.on_complete, on_complete)
        mock_ctk.CTkToplevel.assert_called()

if __name__ == '__main__':
    unittest.main()
