# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **UI/UX Polish**:
  - New Sidebar Navigation with "Home" and "Organizer" views.
  - Dashboard with recent activity and quick actions.
  - Visual feedback for drag-and-drop operations.
  - Progress bar now shows speed (files/sec) and ETA.
  - Application window icon.
- **ML Features**:
  - Improved feedback during ML model loading with progress updates.
  - Smart Categorization now supports text and image content analysis.
- **Documentation**:
  - Added CHANGELOG.md.
  - Updated README with ML details and configuration examples.

### Changed
- Refactored `app.py` to support multiple views.
- Improved `organizer.py` to handle ML model loading feedback via callback wrapper.

### Fixed
- Fixed potential freezing during ML model initialization by providing better user feedback.
