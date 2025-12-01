#!/bin/bash
echo "Setting up Pro File Organizer with uv..."

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "uv is not installed or not in PATH. Please install it from https://github.com/astral-sh/uv"
    exit 1
fi

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment using uv..."
    uv venv
fi

# Activate venv
source venv/bin/activate

# Install requirements (if any)
if [ -f "requirements.txt" ]; then
    uv pip install -r requirements.txt
fi

echo "Setup complete. To run the app:"
echo "source venv/bin/activate"
echo "python app.py"
