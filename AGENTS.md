# Pro File Organizer - Agent Guide 🤖

Welcome! This guide helps AI agents understand the codebase, development workflow, and architecture of the Pro File Organizer project.

## 🛠️ Tech Stack

*   **Language**: Python 3.8+
*   **GUI Framework**: `customtkinter` (Modern UI wrapper around tkinter), `tkinterdnd2` (Drag & Drop).
*   **Machine Learning**: `transformers`, `torch`, `sentence-transformers` (Hugging Face ecosystem).
*   **Image Processing**: `Pillow` (PIL).
*   **File Handling**: `shutil`, `pathlib`.
*   **Package Manager**: `uv` (recommended), or standard `pip`. We commit `uv.lock` to ensure reproducible environments for all contributors.

## 📂 Project Structure

*   **`src/pro_file_organizer/`**: The main package.
    *   **`src/pro_file_organizer/ui/main_window.py`**: The main GUI entry point.
    *   **`src/pro_file_organizer/core/organizer.py`**: Core logic for file organization (`FileOrganizer` class).
    *   **`src/pro_file_organizer/core/ml_organizer.py`**: AI categorization logic (`MultimodalFileOrganizer`).
    *   **`src/pro_file_organizer/core/constants.py`**: Centralized default settings and file paths.
    *   **`src/pro_file_organizer/core/logger.py`**: Centralized logging system.
    *   **`src/pro_file_organizer/ui/components/`**: Reusable UI widgets like `FileCard`.
    *   **`src/pro_file_organizer/ui/dialogs/`**: Configuration and Batch processing windows.
    *   **`src/pro_file_organizer/ui/themes/`**: Custom styles for non-standard widgets.
*   **Runtime State**: Application configuration (`config.json`, `recent.json`) and logs are stored in OS-specific user directories (via `platformdirs`).
    *   **Linux**: `~/.config/pro-file-organizer/` and `~/.local/share/pro-file-organizer/logs/`
    *   **Windows**: `%APPDATA%\Tazztone\pro-file-organizer\`
    *   **macOS**: `~/Library/Application Support/pro-file-organizer/`
*   **`config/` & `logs/`**: These directories in the repository root are for local development and debugging only. They are ignored by git and should not be used for production state.
*   **`scripts/`**: Convenience scripts for environment setup.
*   **`tests/`**: Unit test suite.
*   **`run_app.py`**: Development entry point script.
*   **`pyproject.toml`**: Modern Python project metadata and entry points.

## 🧪 Testing

We use the standard `unittest` framework.

### Running Tests
To run the full suite:
```bash
python -m unittest discover tests
```

### Writing Tests for GUI
*   **Mocking**: We use a stateful `MockBase` (in `tests/ui_test_utils.py`) to mock `customtkinter` widgets. It captures `configure()` calls and provides `cget()` access to verify UI state.
*   **Controller Pattern**: Test the `MainWindowController` directly for logic, mocking the `view` (interface). This allows testing 90%+ of app logic without a physical display.
*   **`sys.modules` Hack**: Used in `setUp` to mock heavy ML libraries (`torch`, `transformers`) and `tkinterdnd2`, enabling fast, headless CI.
*   **Thread Execution**: When testing threaded controller logic (e.g., `run_organization`), mock `threading.Thread` to execute its `target` immediately to avoid race conditions in unit tests.

## 🏗️ Architecture & Behaviors

1.  **Config First**: The app relies on configuration files stored in the `config/` directory. `DEFAULT_CONFIG_FILE` in `constants.py` points there. The `FileOrganizer` class loads this at startup.
2.  **Lazy ML**: Large ML dependencies (`torch`, `transformers`) are NOT imported at top-level in the UI. They are imported inside `ml_organizer.py` or only when strictly needed by `FileOrganizer`. **Do not break this lazy loading**.
3.  **Threading**: File operations and ML inference happen in background threads (`threading.Thread`). The GUI uses callbacks (`log_callback`, `progress_callback`) to update.
4.  **Dry Run**: The `organize_files` method supports `dry_run=True`. This is used for the "Preview" feature.
5.  **Undo Stack**: Operations are pushed to an undo stack. Ensure any new file operation logic supports this.

## 📝 Guidelines

*   **Verify Everything**: After editing code, run the tests (`python -m unittest discover tests`). **Aim to maintain 90%+ total coverage.**
*   **No Artifacts**: Do not edit files in `__pycache__` or `.git`.
*   **Clean Code**: Keep the UI logic separate from the business logic (`organizer.py`) as much as possible. Use the `Controller` for orchestration.
*   **Dependencies**: If adding a new dependency, update `pyproject.toml`.

## 🐛 Troubleshooting

*   **`TclError`**: Usually means you are trying to use a Tkinter widget in a thread other than the main thread, or without a root window.
*   **Model Downloads**: The ML models are large (~2GB). The app handles the download with a progress modal. Do not hardcode paths to models; let `transformers` manage the cache.

Happy Coding! 🚀
