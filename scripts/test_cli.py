import argparse
import os
import sys
from pathlib import Path

from pro_file_organizer.core.organizer import FileOrganizer, OrganizationOptions


def main():
    parser = argparse.ArgumentParser(description="Pro File Organizer CLI (Headless Sandbox Mode)")
    parser.add_argument(
        "source", nargs="?", default="/sandbox", help="Path to the directory to organize (default: /sandbox)"
    )
    parser.add_argument("--recursive", "-r", action="store_true", help="Organize subdirectories")
    parser.add_argument("--ml", action="store_true", help="Enable AI-powered categorization")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without moving files")
    parser.add_argument("--undo", action="store_true", help="Undo the last organization run")

    args = parser.parse_args()
    source_path = Path(args.source).resolve()

    if not source_path.exists() or not source_path.is_dir():
        print(f"Error: {source_path} is not a valid directory.")
        sys.exit(1)

    organizer = FileOrganizer()

    # Allow overriding the undo stack path for Docker persistence
    if "UNDO_STACK_PATH" in os.environ:
        from pro_file_organizer.core import constants

        constants.DEFAULT_UNDO_STACK_FILE = Path(os.environ["UNDO_STACK_PATH"])
        # Re-load to ensure we pick up the mounted file
        organizer._load_undo_stack()

    if args.undo:
        print(f"Undoing last changes in {source_path}...")
        count = organizer.undo_changes(log_callback=print)
        print(f"Undo complete. {count} files restored.")
        return

    options = OrganizationOptions(
        source_path=source_path,
        recursive=args.recursive,
        use_ml=args.ml,
        dry_run=args.dry_run,
        log_callback=print,
        progress_callback=lambda curr, total, name: print(f"[{curr}/{total}] Processing: {name}", end="\r"),
    )

    print(f"Starting organization of: {source_path}")
    if args.dry_run:
        print("!!! DRY RUN ENABLED - No files will be moved !!!")

    result = organizer.organize_files(options)

    print("\n\n--- Results ---")
    print(f"Files moved: {result.get('moved', 0)}")
    print(f"Renamed:     {result.get('renamed', 0)}")
    print(f"Duplicates:  {result.get('duplicates', 0)}")
    print(f"Errors:      {result.get('errors', 0)}")

    if result.get("errors", 0) > 0:
        print("\nReview the logs for error details.")


if __name__ == "__main__":
    main()
