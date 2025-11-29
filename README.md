# Pro File Organizer

A powerful and user-friendly file organizer built with Python and CustomTkinter. This application helps you declutter your folders by automatically sorting files into categories based on their extensions.

## Features

*   **Automatic Sorting**: Sorts files into categories like Images, Videos, Documents, Archives, Audio, Code, and Executables.
*   **Recursive Mode**: Option to organize files inside subfolders ("Include Subfolders").
*   **Date-Based Sorting**: Sort files into `Year/Month` subdirectories (e.g., `Images/2023/November/`).
*   **Undo Functionality**: Safely undo the last 5 organization operations if you made a mistake.
*   **Deep Clean**: Option to delete empty folders after moving files.
*   **Batch Mode**: Process multiple folders at once with individual settings.
*   **Rollback on Error**: Automatically reverts changes if a critical error occurs during processing.
*   **Customizable Settings**:
    *   **Categories**: Add, remove, or modify file categories and extensions.
    *   **Exclusions**: Exclude specific file extensions or folder names from processing.
    *   **Profiles**: Import and export configuration profiles.
*   **Theme Support**: Switch between Light, Dark, and System themes (persisted across sessions).
*   **Real-time Logging**: See what's happening as files are moved, with detailed progress.

## Requirements

*   Python 3.x
*   `customtkinter`
*   `tkinterdnd2`
*   `tkinter` (standard library)

## Installation

1.  Clone the repository or download the source code.
2.  Install dependencies:
    ```bash
    pip install customtkinter tkinterdnd2
    ```
    or
    ```bash
    pip install -r requirements.txt
    ```

## How to Run

Run the application using Python:
```bash
python app.py
```

## Usage

1.  **Browse Folder**: Click the "Browse" button to select the directory you want to organize.
    *   *Tip*: You can also drag and drop a folder into the window.
2.  **Select Options**:
    *   **Include Subfolders**: Check this to also organize files located in subdirectories.
    *   **Sort by Date**: Check this to further organize files into Year/Month folders.
    *   **Delete Empty Folders**: Check this to remove any empty folders left behind.
    *   **Rollback on Error**: Check this to automatically undo changes if an error occurs.
    *   **Dry Run**: simulate the process without moving files.
3.  **Start Organizing**: Click "Start Organizing" to begin.
4.  **Undo**: If you need to revert changes, click "Undo Last Run".

## Shortcuts

*   `<Return>`: Start organizing (after selecting a folder).
*   `<Escape>`: Stop the current process.

## Configuration

*   **Settings**: Click the "Settings" button to manage categories, exclusions, and profiles.
*   **Batch Mode**: Click "Batch Mode" to queue multiple folders for processing.

### config.json Structure

The `config.json` file stores your preferences and category definitions.

```json
{
    "directories": {
        "Images": [".jpg", ".png", ...],
        "Videos": [".mp4", ...],
        ...
    },
    "excluded_names": ["app.py", ...],
    "excluded_extensions": [".tmp", ".log"],
    "excluded_folders": ["node_modules", ".git"],
    "theme_mode": "System"
}
```
