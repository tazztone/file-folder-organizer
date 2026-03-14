#!/bin/bash
# scripts/run_local_cli.sh - Helper script for running the File Organizer CLI locally

set -e

SANDBOX_DIR="$(pwd)/test_sandbox"

show_help() {
    echo "Usage: $0 [command] [args]"
    echo ""
    echo "Commands:"
    echo "  run           Run organization on the sandbox folder"
    echo "  dry-run       Preview organization without moving files"
    echo "  undo          Revert the last organization run"
    echo "  ml-run        Run with AI categorization enabled"
}

case "$1" in
    run)
        shift
        PYTHONPATH=src uv run python scripts/test_cli.py "$SANDBOX_DIR" "$@"
        ;;
    dry-run)
        shift
        PYTHONPATH=src uv run python scripts/test_cli.py "$SANDBOX_DIR" --dry-run "$@"
        ;;
    undo)
        shift
        PYTHONPATH=src uv run python scripts/test_cli.py "$SANDBOX_DIR" --undo "$@"
        ;;
    ml-run)
        shift
        PYTHONPATH=src uv run python scripts/test_cli.py "$SANDBOX_DIR" --ml "$@"
        ;;
    *)
        show_help
        ;;
esac
