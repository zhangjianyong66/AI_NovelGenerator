## Purpose

Specify frontend editing behavior for existing novel project text files and chapter files.

## Requirements

### Requirement: Core project text files can be loaded and saved
The system SHALL allow the frontend to load, edit, save, and display word counts for the core text files in the active output directory.

#### Scenario: User loads core project files
- **WHEN** the frontend opens the workspace for a connected backend and valid output path
- **THEN** it can display `Novel_setting.txt`, `Novel_directory.txt`, `character_state.txt`, and `global_summary.txt` content when those files exist

#### Scenario: User saves edited core file
- **WHEN** the user edits one of the core project text files and saves
- **THEN** the backend writes the updated content to the corresponding file in the active output directory

### Requirement: Chapter files can be navigated and edited
The system SHALL allow the frontend to list, select, navigate, edit, and save chapter files from the active output directory.

#### Scenario: User views chapter list
- **WHEN** the chapters page opens with a valid output path
- **THEN** the frontend displays available chapter files in chapter number order

#### Scenario: User saves a chapter
- **WHEN** the user edits a selected chapter and saves
- **THEN** the backend writes the content to the correct `chapter_X.txt` file and the frontend updates word count and modified state

#### Scenario: User navigates adjacent chapters
- **WHEN** the user chooses previous or next chapter
- **THEN** the frontend selects the adjacent existing chapter without losing unsaved changes silently

### Requirement: Unsaved changes are protected
The system SHALL protect user edits from accidental loss.

#### Scenario: User leaves dirty editor
- **WHEN** the user attempts to switch file, switch chapter, or navigate away while an editor has unsaved changes
- **THEN** the frontend asks the user to save, discard, or cancel the navigation

#### Scenario: Save fails
- **WHEN** the backend fails to save edited content
- **THEN** the frontend keeps the edited content in the editor and displays the failure reason

### Requirement: Existing output format remains compatible
The system SHALL preserve the existing file names and plain-text content format used by the Python GUI and generator.

#### Scenario: File saved by frontend is opened by old GUI
- **WHEN** a core file or chapter file is saved through the frontend
- **THEN** `python main.py` can load the file using existing GUI functions without requiring a format migration
