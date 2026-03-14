#!/bin/bash

# Ensure we are in the script directory
cd "$(dirname "$0")"

# Run the app using uv
uv run python3 run_app.py
