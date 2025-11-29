import unittest
from unittest.mock import MagicMock
import themes

class TestThemes(unittest.TestCase):
    def test_get_palette_light(self):
        palette = themes.get_palette("pro_light")
        self.assertEqual(palette, themes.PALETTES["light"])
        self.assertEqual(palette["bg"], "#f0f0f0")

    def test_get_palette_dark(self):
        palette = themes.get_palette("pro_dark")
        self.assertEqual(palette, themes.PALETTES["dark"])
        self.assertEqual(palette["bg"], "#2d2d2d")

    def test_get_palette_default(self):
        # Should default to dark if unknown
        palette = themes.get_palette("unknown")
        self.assertEqual(palette, themes.PALETTES["dark"])

    def test_setup_themes(self):
        mock_style = MagicMock()
        mock_style.theme_names.return_value = ["clam", "alt"]

        themes.setup_themes(mock_style)

        # Check if theme_create was called for pro_light and pro_dark
        calls = mock_style.theme_create.call_args_list
        theme_names_created = [call[0][0] for call in calls]

        self.assertIn("pro_light", theme_names_created)
        self.assertIn("pro_dark", theme_names_created)

    def test_setup_themes_already_exists(self):
        mock_style = MagicMock()
        mock_style.theme_names.return_value = ["clam", "pro_light", "pro_dark"]

        themes.setup_themes(mock_style)

        # Should not call theme_create
        mock_style.theme_create.assert_not_called()

if __name__ == "__main__":
    unittest.main()
