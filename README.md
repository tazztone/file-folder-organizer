# Pro File Organizer

A powerful and user-friendly file organizer built with Python and Tkinter. This application helps you declutter your folders by automatically sorting files into categories based on their extensions.

## Features

*   **Automatic Sorting**: Sorts files into categories like Images, Videos, Documents, Archives, Audio, Code, and Executables.
*   **Recursive Mode**: Option to organize files inside subfolders ("Include Subfolders").
*   **Date-Based Sorting**: Sort files into `Year/Month` subdirectories (e.g., `Images/2023/November/`).
*   **Undo Functionality**: Safely undo the last organization operation if you made a mistake.
*   **Deep Clean**: Option to delete empty folders after moving files.
*   **Real-time Logging**: See what's happening as files are moved.

## Requirements

*   Python 3.x
*   Tkinter (usually included with Python)

## How to Run

1.  Clone the repository or download `app.py`.
2.  Run the application using Python:
    ```bash
    python app.py
    ```

## Usage

1.  **Browse Folder**: Click the "Browse Folder" button to select the directory you want to organize.
2.  **Select Options**:
    *   **Include Subfolders**: Check this to also organize files located in subdirectories of the selected folder.
    *   **Sort by Date**: Check this to further organize files into Year/Month folders inside their category.
    *   **Delete Empty Folders**: Check this to remove any empty folders left behind after moving files.
3.  **Start Organizing**: Click "Start Organizing" to begin the process.
4.  **Undo**: If you need to revert the changes, click the "Undo Last Run" button.

## Categories

*   **Images**: .jpg, .png, .gif, etc.
*   **Videos**: .mp4, .avi, .mov, etc.
*   **Documents**: .pdf, .docx, .txt, etc.
*   **Archives**: .zip, .rar, .tar, etc.
*   **Audio**: .mp3, .wav, .flac, etc.
*   **Code**: .py, .js, .html, etc.
*   **Executables**: .exe, .msi, .bat, etc.
