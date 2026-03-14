import shutil
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from pro_file_organizer.core.organizer import FileOrganizer, OrganizationOptions


class TestOrganizerExtended(unittest.TestCase):
    def setUp(self):
        self.organizer = FileOrganizer()
        self.tmp_dir = Path("/tmp/organizer_test_ext")
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True)

    def tearDown(self):
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)

    def test_validate_config_errors(self):
        self.organizer.directories[""] = [".txt"]
        self.organizer.directories["Invalid/Slash"] = [".jpg"]
        self.organizer.directories["Dup1"] = [".pdf"]
        self.organizer.directories["Dup2"] = [".pdf"]
        self.organizer.directories["NoDot"] = ["txt"]

        errors = self.organizer.validate_config()
        self.assertTrue(any("empty" in e.lower() for e in errors))
        self.assertTrue(any("separator" in e.lower() for e in errors))
        self.assertTrue(any("duplicate" in e.lower() for e in errors))
        self.assertTrue(any("start with '.'" in e.lower() for e in errors))

    def test_load_config_error(self):
        with patch("builtins.open", mock_open(read_data="invalid json")):
            result = self.organizer.load_config("dummy.json")
            self.assertFalse(result)

    def test_save_config_invalid(self):
        self.organizer.directories[""] = [".txt"]
        result = self.organizer.save_config("dummy.json")
        self.assertFalse(result)

    def test_get_unique_path(self):
        p1 = self.tmp_dir / "test.txt"
        p1.touch()
        unique = self.organizer.get_unique_path(p1)
        self.assertEqual(unique.name, "test_1.txt")

        unique.touch()
        unique2 = self.organizer.get_unique_path(p1)
        self.assertEqual(unique2.name, "test_2.txt")

    def test_scan_files_recursive_exclusions(self):
        (self.tmp_dir / ".git").mkdir()
        (self.tmp_dir / ".git" / "config").touch()
        (self.tmp_dir / "test.txt").touch()

        files = list(self.organizer.scan_files(self.tmp_dir, recursive=True))
        filenames = [f.name for f in files]
        self.assertIn("test.txt", filenames)
        self.assertNotIn("config", filenames)

    def test_organize_files_date_sort_and_logging(self):
        f = self.tmp_dir / "old.txt"
        f.touch()
        mock_log = MagicMock()
        with patch.object(Path, 'stat') as mock_stat:
            mock_stat.return_value.st_mtime = 1600000000
            self.organizer.organize_files(OrganizationOptions(self.tmp_dir, date_sort=True, log_callback=mock_log))
            # Verify logging was called
            mock_log.assert_called()

    def test_organize_files_rollback_on_error(self):
        f = self.tmp_dir / "test.txt"
        f.touch()
        with patch('shutil.move', side_effect=Exception("Move Failed")):
            result = self.organizer.organize_files(OrganizationOptions(self.tmp_dir, rollback_on_error=True))
            self.assertTrue(result.get("rolled_back", False))

    def test_undo_changes_cleanup_empty(self):
        src = self.tmp_dir / "source"
        src.mkdir()
        f = src / "test.txt"
        f.touch()

        self.organizer.organize_files(OrganizationOptions(src))
        self.organizer.undo_changes(log_callback=MagicMock())
        self.assertTrue(f.exists())
        self.assertFalse((src / "Documents").exists())

    def test_ml_lazy_init_failure(self):
        f = self.tmp_dir / "test.txt"
        f.touch()
        # Mock load_models to fail
        with patch('pro_file_organizer.core.ml_organizer.MultimodalFileOrganizer.load_models', side_effect=Exception("ML Fail")):
            mock_log = MagicMock()
            self.organizer.organize_files(OrganizationOptions(self.tmp_dir, use_ml=True, log_callback=mock_log))
            # Should have logged the failure
            log_output = [str(args) for args in mock_log.call_args_list]
            self.assertTrue(any("Failed to load ML models" in s for s in log_output))

    def test_del_empty_folders(self):
        folder = self.tmp_dir / "empty_dir"
        folder.mkdir()
        self.organizer.organize_files(OrganizationOptions(self.tmp_dir, del_empty=True, log_callback=MagicMock()))
        self.assertFalse(folder.exists())

    def test_export_import_config(self):
        cfg = self.tmp_dir / "config.json"
        self.organizer.export_config_file(cfg)
        self.assertTrue(cfg.exists())
        self.assertTrue(self.organizer.import_config_file(cfg))

    def test_theme_mode(self):
        self.organizer.save_theme_mode("Dark")
        self.assertEqual(self.organizer.get_theme_mode(), "Dark")

if __name__ == '__main__':
    unittest.main()
