# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **UI/UX Polish**:
  - **Dashboard**: Added statistics cards (Total Files, Last Run, Batches) to the Home screen.
  - **Drag & Drop**: Improved visual feedback with clearer borders and colors when hovering over the drop zone.
  - **Progress**: Enhanced progress reporting with speed (files/s), ETA, and truncated filenames for better readability.
  - **Icon**: Added a custom generated window icon.
- **ML Features**:
  - **Progress Bar**: Added real-time progress updates for ML model downloading/loading.
  - Smart Categorization now supports text and image content analysis.
- **Documentation**:
  - Added CHANGELOG.md.
  - Updated README with ML details, hardware recommendations, and configuration examples.

### Changed
- Refactored `app.py` to support multiple views.
- Improved `organizer.py` to handle ML model loading feedback via callback wrapper.

### Fixed
- Fixed potential freezing during ML model initialization by providing better user feedback.
