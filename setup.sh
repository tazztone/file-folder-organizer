#!/bin/bash
echo "Setting up Pro File Organizer..."

# Check for python3
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install it first."
    exit 1
fi

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements (if any)
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

echo "Setup complete. To run the app:"
echo "source venv/bin/activate"
echo "python app.py"
