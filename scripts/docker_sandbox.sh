#!/bin/bash
# scripts/docker_sandbox.sh - Helper script for running the File Organizer in Docker

set -e # Exit on error

# Configuration
IMAGE_NAME="file-organizer-sandbox"
DOCKERFILE="Dockerfile.sandbox"
SANDBOX_DIR="$(pwd)/test_sandbox"
MODEL_CACHE="$(pwd)/.model_cache"

# Ensure directories exist
mkdir -p "$SANDBOX_DIR"
mkdir -p "$MODEL_CACHE"

show_help() {
    echo "Usage: $0 [command] [args]"
    echo ""
    echo "Commands:"
    echo "  build         Build the Docker sandbox image"
    echo "  run           Run organization on the sandbox folder"
    echo "  dry-run       Preview organization without moving files"
    echo "  undo          Revert the last organization run"
    echo "  ml-run        Run with AI categorization enabled"
    echo "  gui           Launch the GUI app inside the Docker sandbox"
    echo "  prepare       Reset the test_sandbox with dummy data"
    echo "  shell         Drop into a shell inside the container for debugging"
    echo ""
    echo "Examples:"
    echo "  $0 build"
    echo "  $0 dry-run --recursive"
    echo "  $0 ml-run --recursive"
}

# Default to 'gui' if no command is provided
COMMAND="${1:-gui}"

case "$COMMAND" in
    build)
        echo "Building Docker image: $IMAGE_NAME..."
        docker build -f "$DOCKERFILE" -t "$IMAGE_NAME" .
        ;;
    
    run)
        shift
        echo "Running organization on $SANDBOX_DIR..."
        docker run --rm -v "$SANDBOX_DIR":/sandbox "$IMAGE_NAME" /sandbox "$@"
        ;;

    dry-run)
        shift
        echo "Previewing organization on $SANDBOX_DIR..."
        docker run --rm -v "$SANDBOX_DIR":/sandbox "$IMAGE_NAME" /sandbox --dry-run "$@"
        ;;

    undo)
        shift
        echo "Undoing last changes in $SANDBOX_DIR..."
        docker run --rm -v "$SANDBOX_DIR":/sandbox "$IMAGE_NAME" /sandbox --undo "$@"
        ;;

    ml-run)
        shift
        echo "Running AI-powered organization on $SANDBOX_DIR..."
        echo "Note: Models will be cached in $MODEL_CACHE"
        docker run --rm \
            -v "$SANDBOX_DIR":/sandbox \
            -v "$MODEL_CACHE":/models_cache \
            "$IMAGE_NAME" /sandbox --ml "$@"
        ;;

    gui)
        echo "Starting GUI in Docker Sandbox..."
        # Allow X11 connections (required for some Linux setups)
        xhost +local:docker > /dev/null || true
        
        docker run --rm \
            -e DISPLAY=$DISPLAY \
            -v /tmp/.X11-unix:/tmp/.X11-unix \
            -v "$SANDBOX_DIR":/sandbox \
            -v "$MODEL_CACHE":/models_cache \
            --entrypoint python \
            "$IMAGE_NAME" run_app.py
        ;;

    prepare)
        echo "Resetting sandbox dummy data..."
        python3 scripts/prepare_sandbox.py
        ;;

    shell)
        echo "Starting debug shell..."
        docker run -it --rm \
            -v "$SANDBOX_DIR":/sandbox \
            -v "$MODEL_CACHE":/models_cache \
            --entrypoint /bin/bash \
            "$IMAGE_NAME"
        ;;

    *)
        # If an unknown command was typed, show help
        if [ "$COMMAND" != "gui" ]; then
            show_help
        else
            # This handles the case where gui was specifically requested but failed earlier
            show_help
        fi
        ;;
esac
