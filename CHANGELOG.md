# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Framework Migration**: Migrated the entire UI layer from `customtkinter` to **PySide6**.
  - Improved performance and cross-platform stability.
  - Native drag-and-drop support using Qt events.
  - QSS-based theming system with dynamic Light/Dark/System mode support.
- **UI/UX Polish**:
  - Replaced plain checkboxes with custom animated **Toggle Switches**.
  - Restored separate Results Header for better visual hierarchy during processing.
  - Refined dashboard layout with improved spacing and typography.
- **CI/CD Improvements**:
  - Updated CI pipeline to use `xvfb` for headless Linux testing.
  - Switched test runner to `pytest` for better integration with project configuration.
- **Reliability**:
  - Fixed a critical infinite loop bug in layout clearing that caused memory exhaustion.
  - Added robust PySide6 mocks for the test suite.

## [0.1.0] - 2026-03-13

### Added
- **UI/UX Polish**:
