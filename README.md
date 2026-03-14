# Pro File Organizer 📂

A powerful, modern file organizer application built with Python and PySide6. It uses intelligent rules and AI to organize your messy folders into a clean, structured hierarchy.

![Dashboard Placeholder](https://via.placeholder.com/800x500?text=Pro+File+Organizer+Dashboard)

## Features ✨

*   **Smart Organization**: Automatically sorts files into categories (Images, Videos, Documents, etc.).
*   **AI-Powered Categorization** 🧠:
    *   Uses **Multimodal AI** (Qwen for text, SigLIP for images) to understand file content.
    *   Categorizes "screenshot.png" into "Images/Screenshots" or "invoice.pdf" into "Documents/Financial".
*   **Modern UI**: Clean, dark-mode friendly interface using PySide6 and QSS.
*   **Dashboard**: Track your organization stats and history.
*   **Drag & Drop**: Simply drag a folder into the window to start.
*   **Batch Processing**: Organize multiple folders with different settings in one go.
*   **Undo Support**: Made a mistake? Undo changes with a single click.
*   **Customizable**: Define your own categories and extensions.
*   **Performance**: Process thousands of files in seconds (with hardware acceleration support).

## Installation 🛠️

### Prerequisites
*   Python 3.10+
*   [uv](https://github.com/astral-sh/uv) (a fast Python package installer)
*   (Optional) NVIDIA GPU for faster AI processing

### Setup
1.  Clone the repository:
    ```bash
    git clone https://github.com/tazztone/file-folder-organizer.git
    cd file-folder-organizer
    ```
2.  Run the setup script:
    *   **Windows**: Double-click `scripts/setup.bat`
    *   **Linux/macOS**: Run `bash scripts/setup.sh`

    The setup script will create a virtual environment and install all necessary dependencies using `uv`.

    Or install as a package:
    ```bash
    uv venv
    source venv/bin/activate
    pip install .
    ```


## Usage 🚀

1.  **Launch the App**:
    ```bash
    uv run run_app.py
    ```
    Alternatively, if installed as a package:
    ```bash
    pro-file-organizer
    ```
2.  **Select a Folder**:
    *   Drag and drop a folder onto the target area.
    *   Or click "Browse" to select manually.
3.  **Choose Options**:
    *   **Include Subfolders**: Deep scan.
    *   **Sort by Date**: Organizes into `Year/Month` subfolders.
    *   **Smart Categorization (AI)**: Enable for content-based sorting (requires ~3GB model download on first run).
4.  **Start**: Click "ORGANIZE".

## Sandbox Testing & Safety 🛡️

Testing a file organizer on real data can be risky. We provide multiple layers of safety:

### 1. "Hard Stop" Safety
The core `FileOrganizer` logic includes a built-in safety check that refuses to move or restore any file outside of the user-provided target directory, preventing "escape" bugs.

### 2. Manual Sandbox
Run the sandbox preparation script to create a messy folder with dummy data for testing:
```bash
python3 scripts/prepare_sandbox.py
```
Then, test the app using the CLI wrapper (headless) or the GUI against the `test_sandbox/` folder.

### 3. Docker Isolation (Recommended for Real Data)
For 100% isolation, run the app inside a Docker container. This ensures the app **physically cannot see** any files on your host except for the ones you explicitly mount.

**Build the sandbox:**
```bash
docker build -f Dockerfile.sandbox -t file-organizer-sandbox .
```

**Run the sandbox (Dry Run):**
```bash
docker run --rm \
  -v $(pwd)/test_sandbox:/sandbox \
  file-organizer-sandbox /sandbox --dry-run
```

**Run the sandbox (Real):**
```bash
docker run --rm \
  -v $(pwd)/test_sandbox:/sandbox \
  file-organizer-sandbox /sandbox
```

## AI Models & ML 🤖

When enabled, the app uses local AI models to inspect file content:
*   **Images**: Analyzed by `google/siglip2-base-patch32-256` to detect scene/content (e.g., Personal, Screenshots, Diagrams).
*   **Documents/Text**: Analyzed by `Qwen/Qwen3-Embedding-0.6B` to classify based on semantic content (e.g., Financial, Code, Reports).

**Note**: The first run will download approximately **3GB** of model data. This is cached locally.
**Hardware**: NVIDIA GPU (CUDA) or Apple Silicon (MPS) is recommended for best performance. CPU mode is supported but slower.

## Configuration ⚙️

You can customize categories via the "Settings" menu or by editing `config/config.json`.

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
uv run pytest
```

To run tests with coverage:
```bash
uv run coverage run -m pytest tests/
uv run coverage report
```

### Agents 🤖

If you are an AI agent working on this codebase, please refer to [AGENTS.md](AGENTS.md) for specific instructions and guidelines.

## Screenshots 📸

*(Add screenshots of the Main Dashboard, Organizer View, and Settings Dialog here)*

## License 📄

MIT License
