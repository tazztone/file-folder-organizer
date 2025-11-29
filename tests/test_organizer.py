import unittest
import shutil
import tempfile
import os
import json
from pathlib import Path
from organizer import FileOrganizer

class TestFileOrganizer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.organizer = FileOrganizer()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_file(self, filename, content="test"):
        path = os.path.join(self.test_dir, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return Path(path)

    def test_get_unique_path(self):
        self.create_file("test.txt")
        p = Path(self.test_dir) / "test.txt"
        unique_p = self.organizer.get_unique_path(p)
        self.assertEqual(unique_p, Path(self.test_dir) / "test_1.txt")

    def test_organize_basic(self):
        self.create_file("image.jpg")
        self.create_file("doc.pdf")

        stats = self.organizer.organize_files(Path(self.test_dir))

        self.assertEqual(stats["moved"], 2)
        self.assertTrue((Path(self.test_dir) / "Images" / "image.jpg").exists())
        self.assertTrue((Path(self.test_dir) / "Documents" / "doc.pdf").exists())

    def test_dry_run(self):
        self.create_file("image.jpg")

        stats = self.organizer.organize_files(Path(self.test_dir), dry_run=True)

        self.assertEqual(stats["moved"], 1)
        # File should NOT have moved
        self.assertTrue((Path(self.test_dir) / "image.jpg").exists())
        self.assertFalse((Path(self.test_dir) / "Images" / "image.jpg").exists())

    def test_recursive(self):
        self.create_file("sub/image.png")

        self.organizer.organize_files(Path(self.test_dir), recursive=True)

        self.assertTrue((Path(self.test_dir) / "Images" / "image.png").exists())

    def test_date_sort(self):
        f = self.create_file("photo.jpg")
        ts = 1672574400 # 2023-01-01
        os.utime(f, (ts, ts))

        self.organizer.organize_files(Path(self.test_dir), date_sort=True)

        self.assertTrue((Path(self.test_dir) / "Images" / "2023").exists())

    def test_delete_empty(self):
        os.makedirs(os.path.join(self.test_dir, "empty"))
        self.organizer.organize_files(Path(self.test_dir), del_empty=True)
        self.assertFalse((Path(self.test_dir) / "empty").exists())

    def test_undo(self):
        self.create_file("doc.txt")
        self.organizer.organize_files(Path(self.test_dir))

        self.assertFalse((Path(self.test_dir) / "doc.txt").exists())

        self.organizer.undo_changes()

        self.assertTrue((Path(self.test_dir) / "doc.txt").exists())

    def test_custom_config(self):
        config = {"Custom": [".xyz"]}
        config_path = os.path.join(self.test_dir, "config.json")
        with open(config_path, "w") as f:
            json.dump(config, f)

        self.organizer.load_config(config_path)
        self.create_file("test.xyz")

        self.organizer.organize_files(Path(self.test_dir))

        self.assertTrue((Path(self.test_dir) / "Custom" / "test.xyz").exists())

if __name__ == "__main__":
    unittest.main()
