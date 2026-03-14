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
    echo "  prepare       Reset the test_sandbox with dummy data"
    echo "  shell         Drop into a shell inside the container for debugging"
    echo ""
    echo "Examples:"
    echo "  $0 build"
    echo "  $0 dry-run --recursive"
    echo "  $0 ml-run --recursive"
}

case "$1" in
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
        show_help
        ;;
esac
