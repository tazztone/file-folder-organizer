import unittest
from unittest.mock import MagicMock
import organizer

class TestSettingsValidation(unittest.TestCase):
    def setUp(self):
        self.organizer = organizer.FileOrganizer()

    def test_validate_config_valid(self):
        self.organizer.directories = {
            "Images": [".jpg", ".png"]
        }
        errors = self.organizer.validate_config()
        self.assertEqual(len(errors), 0)

    def test_validate_config_empty_category(self):
        self.organizer.directories = {
            "": [".jpg"]
        }
        errors = self.organizer.validate_config()
        self.assertTrue(any("empty" in e for e in errors))

    def test_validate_config_invalid_extension(self):
        self.organizer.directories = {
            "Images": ["jpg"] # Missing dot
        }
        errors = self.organizer.validate_config()
        self.assertTrue(any("Must start with '.'" in e for e in errors))

    def test_validate_config_duplicate_extension(self):
        self.organizer.directories = {
            "Images": [".jpg"],
            "Photos": [".jpg"]
        }
        errors = self.organizer.validate_config()
        self.assertTrue(any("Duplicate extension" in e for e in errors))

if __name__ == "__main__":
    unittest.main()
