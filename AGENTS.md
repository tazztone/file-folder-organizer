# Pro File Organizer - Agent Guide 🤖

Welcome! This guide helps AI agents understand the codebase, development workflow, and architecture of the Pro File Organizer project.

## 🛠️ Tech Stack

*   **Language**: Python 3.8+
*   **GUI Framework**: `customtkinter` (Modern UI wrapper around tkinter), `tkinterdnd2` (Drag & Drop).
*   **Machine Learning**: `transformers`, `torch`, `sentence-transformers` (Hugging Face ecosystem).
*   **Image Processing**: `Pillow` (PIL).
*   **File Handling**: `shutil`, `pathlib`.
*   **Package Manager**: `uv` (recommended), or standard `pip`.

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
*   **`config/`**: Contains application state and configuration files (`config.json`, `recent.json`, etc.).
*   **`logs/`**: Directory for application logs.
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
*   **Mocking**: Since this is a GUI app, you **must** mock `tkinter`, `customtkinter`, and `tkinterdnd2` in many cases to avoid "display not found" errors or creating actual windows during tests.
*   **`sys.modules` Hack**: You may see patterns where `sys.modules` is modified in `setUp` to mock entire modules before import. Respect this pattern.
*   **Thread Safety**: UI updates from background threads must be scheduled using `window.after`. Tests should verify this behavior where applicable.

## 🏗️ Architecture & Behaviors

1.  **Config First**: The app relies on configuration files stored in the `config/` directory. `DEFAULT_CONFIG_FILE` in `constants.py` points there. The `FileOrganizer` class loads this at startup.
2.  **Lazy ML**: Large ML dependencies (`torch`, `transformers`) are NOT imported at top-level in the UI. They are imported inside `ml_organizer.py` or only when strictly needed by `FileOrganizer`. **Do not break this lazy loading**.
3.  **Threading**: File operations and ML inference happen in background threads (`threading.Thread`). The GUI uses callbacks (`log_callback`, `progress_callback`) to update.
4.  **Dry Run**: The `organize_files` method supports `dry_run=True`. This is used for the "Preview" feature.
5.  **Undo Stack**: Operations are pushed to an undo stack. Ensure any new file operation logic supports this.

## 📝 Guidelines

*   **Verify Everything**: After editing code, run the tests (`python -m unittest discover tests`).
*   **No Artifacts**: Do not edit files in `__pycache__` or `.git`.
*   **Clean Code**: Keep the UI logic separate from the business logic (`organizer.py`) as much as possible.
*   **Dependencies**: If adding a new dependency, update `requirements.txt`.

## 🐛 Troubleshooting

*   **`TclError`**: Usually means you are trying to use a Tkinter widget in a thread other than the main thread, or without a root window.
*   **Model Downloads**: The ML models are large (~2GB). The app handles the download with a progress modal. Do not hardcode paths to models; let `transformers` manage the cache.

Happy Coding! 🚀
