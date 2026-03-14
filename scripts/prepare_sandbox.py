import os
import shutil
from pathlib import Path


def create_dummy_file(path, size_kb=1):
    """Creates a dummy file of a certain size."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(os.urandom(size_kb * 1024))

def setup_sandbox(sandbox_path: Path):
    if sandbox_path.exists():
        print(f"Cleaning existing sandbox at {sandbox_path}...")
        shutil.rmtree(sandbox_path)

    sandbox_path.mkdir(parents=True, exist_ok=True)
    print(f"Creating sandbox at {sandbox_path}...")

    # Create a messy structure
    files = [
        "vacation_photo1.jpg",
        "vacation_photo2.png",
        "work/project_proposal.pdf",
        "work/budget_2024.xlsx",
        "work/notes.txt",
        "downloads/setup.exe",
        "downloads/archive.zip",
        "scripts/utils.py",
        "scripts/test.sh",
        "random_file.unknown",
        "README.md",
        "todo.txt",
        "music/song1.mp3",
        "videos/movie.mp4",
        "nested/deep/folder/screenshot.png"
    ]

    for f in files:
        create_dummy_file(sandbox_path / f)

    print("\nSandbox prepared! You can now test the app on this folder.")
    print(f"Path: {sandbox_path.absolute()}")
    print("\nSuggested tests:")
    print("1. Run 'uv run run_app.py'")
    print(f"2. Select the folder: {sandbox_path.absolute()}")
    print("3. Try 'Dry Run' first to see what it would do.")
    print("4. Try 'Organize' and check the results.")
    print("5. Try 'Undo' to restore the messy state.")

if __name__ == "__main__":
    sandbox_dir = Path.cwd() / "test_sandbox"
    setup_sandbox(sandbox_dir)
