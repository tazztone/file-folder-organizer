import importlib
import sys
import unittest
from unittest.mock import MagicMock, patch

from tests.ui_test_utils import get_ui_mocks

# Apply standardized mocks
mock_ctk, mock_dnd = get_ui_mocks()
sys.modules["customtkinter"] = mock_ctk
sys.modules["tkinterdnd2"] = mock_dnd

# Reload main_window
import pro_file_organizer.ui.main_window  # noqa: E402

importlib.reload(pro_file_organizer.ui.main_window)
from pro_file_organizer.ui.main_window import OrganizerApp  # noqa: E402


class TestMainWindow(unittest.TestCase):
    def setUp(self):
        self.patchers = [
            patch("pro_file_organizer.ui.main_window.FileOrganizer"),
            patch("pro_file_organizer.ui.main_window.MultimodalFileOrganizer"),
            patch("pro_file_organizer.ui.main_window.MainWindowController"),
            patch("pro_file_organizer.ui.main_window.SettingsDialog"),
            patch("pro_file_organizer.ui.main_window.BatchDialog"),
            patch("pro_file_organizer.ui.main_window.messagebox"),
            patch("pro_file_organizer.ui.main_window.filedialog"),
        ]
        self.mocks = [p.start() for p in self.patchers]
        self.app = OrganizerApp()

    def tearDown(self):
        for p in self.patchers:
            p.stop()

    def test_init(self):
        self.assertIsNotNone(self.app.controller)

    def test_update_folder_display(self):
        self.app.update_folder_display("/tmp/test")
        self.assertEqual(self.app.lbl_drop.cget("text"), "Selected: test")
        self.assertEqual(self.app.btn_run.cget("state"), "normal")

    def test_clear_results(self):
        mock_child = MagicMock()
        self.app.scroll_results.winfo_children.return_value = [mock_child]
        self.app.clear_results()
        mock_child.destroy.assert_called()

    def test_show_status(self):
        self.app.show_status("Busy...")
        self.assertEqual(self.app.lbl_status.cget("text"), "Busy...")

    def test_update_progress(self):
        # Numeric progress
        self.app.update_progress(5, 10, "file.txt")
        self.app.progress_bar.set.assert_called_with(0.5)

        # Float progress (ML loading)
        self.app.update_progress(0.7, 1.0, "Model Loading")
        self.app.progress_bar.set.assert_called_with(0.7)

    def test_ui_toggles(self):
        self.app.enable_ai_ui()
        self.app.frame_ai_conf.pack.assert_called()

        self.app.disable_ai_ui()
        self.app.frame_ai_conf.pack_forget.assert_called()

    def test_set_running_state(self):
        self.app.set_running_state(True)
        self.assertEqual(self.app.btn_run.cget("state"), "disabled")
        self.assertEqual(self.app.scroll_results.cget("label_text"), "Processing...")

    def test_open_dialogs(self):
        self.app.open_settings()
        self.app.controller.open_settings.assert_called()

        self.app.open_batch()
        self.app.controller.open_batch.assert_called()

    def test_change_appearance(self):
        with patch("pro_file_organizer.ui.main_window.ctk.set_appearance_mode") as mock_set:
            self.app.change_appearance_mode_event("Dark")
            mock_set.assert_called_with("Dark")
            self.app.organizer.save_theme_mode.assert_called_with("Dark")

    def test_on_drop(self):
        event = MagicMock()
        event.data = "/tmp/drop"
        self.app.on_drop(event)
        self.app.controller.set_folder.assert_called_with("/tmp/drop")

        # Braced path
        event.data = "{/tmp/spaced path}"
        self.app.on_drop(event)
        self.app.controller.set_folder.assert_called_with("/tmp/spaced path")

    def test_show_error(self):
        self.app.show_error("Title", "Message")
        self.mocks[5].showerror.assert_called_with("Title", "Message")

    def test_show_info(self):
        self.app.show_info("Title", "Message")
        self.mocks[5].showinfo.assert_called_with("Title", "Message")

    def test_confirm_action(self):
        self.app.confirm_action("Title", "Message")
        self.mocks[5].askyesno.assert_called_with("Title", "Message")

    def test_update_stats_display(self):
        stats = {"total_files": 100, "last_run": "Today"}
        self.app.update_stats_display(stats)
        self.assertEqual(self.app.lbl_stats_total.cget("text"), "Files Organized: 100")
        self.assertEqual(self.app.lbl_stats_last.cget("text"), "Last Run: Today")

    def test_show_model_download(self):
        with patch("pro_file_organizer.ui.main_window.ModelDownloadModal") as mock_modal:
            callback = MagicMock()
            self.app.show_model_download(callback)
            mock_modal.assert_called_with(self.app, on_complete=callback)

    def test_show_settings(self):
        with patch("pro_file_organizer.ui.main_window.SettingsDialog") as mock_dialog:
            self.app.show_settings(self.app.organizer)
            mock_dialog.assert_called_with(self.app, self.app.organizer)

    def test_show_batch(self):
        with patch("pro_file_organizer.ui.main_window.BatchDialog") as mock_dialog:
            self.app.show_batch(self.app.organizer)
            mock_dialog.assert_called_with(self.app, self.app.organizer)

    def test_set_ai_switch_state(self):
        self.app.set_ai_switch_state(True)
        self.app.switch_ai.select.assert_called()
        self.app.set_ai_switch_state(False)
        self.app.switch_ai.deselect.assert_called()

    def test_set_watch_switch_state(self):
        self.app.set_watch_switch_state(True)
        self.app.chk_watch.select.assert_called()
        self.app.set_watch_switch_state(False)
        self.app.chk_watch.deselect.assert_called()

    def test_getters(self):
        self.app.slider_conf.get.return_value = 0.5
        self.assertEqual(self.app.get_ai_confidence(), 0.5)

    def test_browse_folder(self):
        with patch("pro_file_organizer.ui.main_window.CTkFolderPicker") as mock_picker:
            self.app.controller.selected_path = "/tmp"
            self.app.browse_folder()
            mock_picker.assert_called_with(self.app, initial_dir="/tmp", on_select=self.app.controller.set_folder)

    def test_drag_drop_visuals(self):
        event = MagicMock()
        with patch.object(self.app, "_draw_dashed_border") as mock_draw:
            self.app._on_drag_enter(event)
            mock_draw.assert_called()
            self.app._on_drag_leave(event)
            self.assertEqual(mock_draw.call_count, 2)

    def test_appearance_mode_changed(self):
        with patch.object(self.app, "_draw_dashed_border") as mock_draw:
            self.app._on_appearance_mode_changed("Dark")
            # Uses app.after, which our MockBase executes immediately
            mock_draw.assert_called()

    def test_draw_dashed_border(self):
        # Verify it doesn't crash and calls canvas methods
        self.app.drop_canvas.winfo_width.return_value = 100
        self.app.drop_canvas.winfo_height.return_value = 100
        self.app._draw_dashed_border()
        self.app.drop_canvas.create_rectangle.assert_called()

        self.app.var_recursive.set(True)
        self.assertEqual(self.app.get_recursive_val(), True)

        self.app.var_date_sort.set(False)
        self.assertEqual(self.app.get_date_sort_val(), False)

        self.app.var_del_empty.set(True)
        self.assertEqual(self.app.get_del_empty_val(), True)

        self.app.var_detect_duplicates.set(False)
        self.assertEqual(self.app.get_detect_duplicates_val(), False)

    def test_add_result_card(self):
        with patch("pro_file_organizer.ui.main_window.FileCard") as mock_card:
            data = {"file": "test.txt", "category": "Docs"}
            self.app.add_result_card(data)
            self.assertEqual(len(self.app.result_cards), 1)
            mock_card.assert_called()

    def test_update_results_header(self):
        self.app.update_results_header("New Header")
        self.app.scroll_results.configure.assert_called_with(label_text="New Header")


if __name__ == "__main__":
    unittest.main()
