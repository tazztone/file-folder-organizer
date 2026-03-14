import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tests.ui_test_utils import get_pyside_mocks

# Apply standardized mocks
mock_qtwidgets, mock_qtcore, mock_qtgui = get_pyside_mocks()
sys.modules["PySide6.QtWidgets"] = mock_qtwidgets
sys.modules["PySide6.QtCore"] = mock_qtcore
sys.modules["PySide6.QtGui"] = mock_qtgui

from pro_file_organizer.core import organizer
from pro_file_organizer.ui.dialogs import batch_dialog


class TestBatchDialog(unittest.TestCase):
    def setUp(self):
        self.mock_parent = MagicMock()
        self.organizer = organizer.FileOrganizer()

        # Patch json load/dump
        self.json_patch = patch("pro_file_organizer.ui.dialogs.batch_dialog.json")
        self.mock_json = self.json_patch.start()
        self.mock_json.load.return_value = []

        # Patch exists
        self.exists_patch = patch("pro_file_organizer.ui.dialogs.batch_dialog.Path.exists", return_value=True)
        self.mock_exists = self.exists_patch.start()

        self.dialog = batch_dialog.BatchDialog(self.mock_parent, self.organizer)

    def tearDown(self):
        self.json_patch.stop()
        self.exists_patch.stop()

    def test_init(self):
        self.assertEqual(self.dialog.batch_folders, [])
        self.dialog.setWindowTitle.assert_called_with("Batch Organization")

    def test_add_folder(self):
        mock_qtwidgets.QFileDialog.getExistingDirectory.return_value = "/tmp/new_folder"
        self.dialog.add_folder()

        self.assertEqual(len(self.dialog.batch_folders), 1)
        self.assertEqual(self.dialog.batch_folders[0]["path"], "/tmp/new_folder")

    def test_add_duplicate_folder(self):
        self.dialog.batch_folders = [{"path": "/tmp/folder", "settings": None}]
        mock_qtwidgets.QFileDialog.getExistingDirectory.return_value = "/tmp/folder"
        self.dialog.add_folder()
        self.assertEqual(len(self.dialog.batch_folders), 1)

    def test_remove_folder(self):
        self.dialog.batch_folders = [
            {"path": "/tmp/folder1", "settings": None},
            {"path": "/tmp/folder2", "settings": None},
        ]
        self.dialog.remove_folder(0)
        self.assertEqual(len(self.dialog.batch_folders), 1)
        self.assertEqual(self.dialog.batch_folders[0]["path"], "/tmp/folder2")

    def test_clear_all(self):
        self.dialog.batch_folders = [{"path": "/tmp/folder", "settings": None}]
        mock_qtwidgets.QMessageBox.question.return_value = 1 # QMessageBox.Yes
        self.dialog.clear_all()
        self.assertEqual(self.dialog.batch_folders, [])

    def test_run_batch_empty(self):
        self.dialog.batch_folders = []
        self.dialog.run_batch()
        mock_qtwidgets.QMessageBox.warning.assert_called()

    def test_run_batch_execution(self):
        self.dialog.batch_folders = [{"path": "/tmp/folder", "settings": None}]
        mock_qtwidgets.QMessageBox.question.return_value = 1 # QMessageBox.Yes
        
        with patch("threading.Thread") as mock_thread:
            self.dialog.run_batch()
            mock_thread.assert_called_once()
            target = mock_thread.call_args[1].get("target")

            self.organizer.organize_files = MagicMock()
            target()

            self.organizer.organize_files.assert_called_with(
                Path("/tmp/folder"), recursive=False, date_sort=False, del_empty=False, dry_run=False
            )
            # Should emit signals
            self.dialog.signals.status_updated.emit.assert_called()
            self.dialog.signals.progress_updated.emit.assert_called()


if __name__ == "__main__":
    unittest.main()
