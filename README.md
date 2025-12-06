# Pro File Organizer 📂

A powerful, modern file organizer application built with Python and CustomTkinter. It uses intelligent rules and AI to organize your messy folders into a clean, structured hierarchy.

![Dashboard Placeholder](https://via.placeholder.com/800x500?text=Pro+File+Organizer+Dashboard)

## Features ✨

*   **Smart Organization**: Automatically sorts files into categories (Images, Videos, Documents, etc.).
*   **AI-Powered Categorization** 🧠:
    *   Uses **Multimodal AI** (Qwen for text, SigLIP for images) to understand file content.
    *   Categorizes "screenshot.png" into "Images/Screenshots" or "invoice.pdf" into "Documents/Financial".
*   **Modern UI**: Clean, dark-mode friendly interface using CustomTkinter.
*   **Dashboard**: Track your organization stats and history.
*   **Drag & Drop**: Simply drag a folder into the window to start.
*   **Batch Processing**: Organize multiple folders with different settings in one go.
*   **Undo Support**: Made a mistake? Undo changes with a single click.
*   **Customizable**: Define your own categories and extensions.
*   **Performance**: Process thousands of files in seconds (with hardware acceleration support).

## Installation 🛠️

### Prerequisites
*   Python 3.8+
*   [uv](https://github.com/astral-sh/uv) (a fast Python package installer)
*   (Optional) NVIDIA GPU for faster AI processing

### Setup
1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusername/pro-file-organizer.git
    cd pro-file-organizer
    ```
2.  Run the setup script:
    *   **Windows**: Double-click `setup.bat`
    *   **Linux/macOS**: Run `bash setup.sh`

    The setup script will create a virtual environment and install all necessary dependencies using `uv`.

    Or install manually with `uv`:
    ```bash
    uv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    uv pip install -r requirements.txt
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
**Hardware**: NVIDIA GPU (CUDA) or Apple Silicon (MPS) is recommended for best performance. CPU mode is supported but slower.

## Configuration ⚙️

You can customize categories via the "Settings" menu or by editing `config.json`.

### Basic Configuration
The `directories` key maps category names to lists of file extensions.

```json
{
  "directories": {
    "Images": [".jpg", ".png", ".gif"],
    "Documents": [".pdf", ".docx", ".txt"],
    "MyScripts": [".py", ".sh"]
  }
}
```

### ML Configuration
To customize how AI categorizes your files, modify `ml_categories`. You can define categories that rely on visual content (for images) or text content (for documents).

*   **visual**: A list of descriptions or keywords that describe the image content.
*   **text**: Keywords or a description of the text content.

```json
{
  "ml_categories": {
    "Images/Memes": {
      "visual": ["funny meme", "internet meme", "text on image"]
    },
    "Documents/Invoices": {
      "text": "invoice total amount due payment bill receipt"
    },
    "Images/Nature": {
        "visual": ["forest", "mountain", "river", "landscape"]
    }
  },
  "ml_confidence": 0.3
}
```

### Exclusions
You can exclude specific files, extensions, or folders from being processed.

```json
{
  "excluded_extensions": [".tmp", ".log"],
  "excluded_folders": [".git", "node_modules", "venv"]
}
```

## Development 💻

### Running Tests

To run the full test suite:
```bash
python -m unittest discover tests
```

### Agents 🤖

If you are an AI agent working on this codebase, please refer to [AGENTS.md](AGENTS.md) for specific instructions and guidelines.

## Screenshots 📸

*(Add screenshots of the Main Dashboard, Organizer View, and Settings Dialog here)*

## License 📄

MIT License
