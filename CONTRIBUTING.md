# Contributing to Pro File Organizer

Thank you for your interest in contributing! This project aims to be a robust and intelligent file organization tool.

## 🛠️ Environment Setup

We use `uv` for dependency management.

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    uv pip install -e .
    # For ML features:
    uv pip install -e ".[ml]"
    # For development tools:
    uv pip install ruff coverage
    ```

## 🧪 Testing Standards

- **Maintain Coverage**: We aim for 90%+ total coverage.
- **Run Tests**: `python -m unittest discover tests`
- **Check Linting**: `ruff check .`

## 🏗️ Pull Request Workflow

1.  Create a feature branch from `main`.
2.  Make your changes.
3.  Ensure tests pass and linting is clean.
4.  Submit a PR with a clear description of the changes.

## 🤖 AI Agents

AI agents should refer to [AGENTS.md](AGENTS.md) for detailed architecture and mocking instructions.
