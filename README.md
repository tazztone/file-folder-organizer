# Pro File Organizer 📂

A powerful, modern file organizer application built with Python and CustomTkinter. It uses intelligent rules and AI to organize your messy folders into a clean, structured hierarchy.

![Dashboard Placeholder](https://via.placeholder.com/800x500?text=Pro+File+Organizer+Dashboard)

## Features ✨

*   **Smart Organization**: Automatically sorts files into categories (Images, Videos, Documents, etc.).
*   **AI-Powered Categorization** 🧠:
    *   Uses **Multimodal AI** (Qwen for text, SigLIP for images) to understand file content.
    *   Categorizes "screenshot.png" into "Images/Screenshots" or "invoice.pdf" into "Documents/Financial".
*   **Modern UI**: Clean, dark-mode friendly interface using CustomTkinter.
*   **Drag & Drop**: Simply drag a folder into the window to start.
*   **Batch Processing**: Organize multiple folders with different settings in one go.
*   **Undo Support**: Made a mistake? Undo changes with a single click.
*   **Customizable**: Define your own categories and extensions.
*   **Performance**: Process thousands of files in seconds (with hardware acceleration support).

## Installation 🛠️

### Prerequisites
*   Python 3.8+
*   (Optional) NVIDIA GPU for faster AI processing

### Setup
1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusername/pro-file-organizer.git
    cd pro-file-organizer
    ```
2.  Run the setup script:
    *   **Windows**: Double-click `setup.bat`
    *   **Linux/macOS**: Run `./setup.sh`

    Or install manually:
    ```bash
    pip install -r requirements.txt
    ```

## Usage 🚀

1.  **Launch the App**:
    ```bash
    python app.py
    ```
2.  **Select a Folder**:
    *   Drag and drop a folder onto the target area.
    *   Or click "Browse" to select manually.
3.  **Choose Options**:
    *   **Include Subfolders**: Deep scan.
    *   **Sort by Date**: Organizes into `Year/Month` subfolders.
    *   **Smart Categorization (AI)**: Enable for content-based sorting (requires ~2GB model download on first run).
4.  **Start**: Click "Start Organizing".

## Smart Categorization (AI) 🤖

When enabled, the app uses local AI models to inspect file content:
*   **Images**: Analyzed by `google/siglip2-base-patch32-256` to detect scene/content (e.g., Personal, Screenshots, Diagrams).
*   **Documents/Text**: Analyzed by `Qwen/Qwen3-Embedding-0.6B` to classify based on semantic content (e.g., Financial, Code, Reports).

**Note**: The first run will download approximately **2GB** of model data. This is cached locally.
**Hardware**: GPU is recommended but runs on CPU (slower).

## Configuration ⚙️

You can customize categories via the "Settings" menu or by editing `config.json`.

### Example `config.json`:
```json
{
  "directories": {
    "Images": [".jpg", ".png", ".gif"],
    "Documents": [".pdf", ".docx", ".txt"],
    "MyScripts": [".py", ".sh"]
  },
  "ml_categories": {
    "Images/Memes": {
      "visual": ["funny meme", "internet meme", "text on image"]
    },
    "Documents/Invoices": {
      "text": "invoice total amount due payment bill receipt"
    }
  },
  "excluded_extensions": [".tmp", ".log"],
  "excluded_folders": [".git", "node_modules"]
}
```

## Screenshots 📸

*(Add screenshots of the Main Dashboard, Organizer View, and Settings Dialog here)*

## License 📄

MIT License
