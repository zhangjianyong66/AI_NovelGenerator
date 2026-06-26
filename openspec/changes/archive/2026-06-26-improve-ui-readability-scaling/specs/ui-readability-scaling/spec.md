## ADDED Requirements

### Requirement: Comfort UI scaling is applied globally
The application SHALL apply a comfort-level CustomTkinter widget scaling setting before building the main GUI so that common controls render larger than the current default.

#### Scenario: Application starts with comfort scaling
- **WHEN** the user starts the desktop application
- **THEN** the main window SHALL build with comfort-level widget scaling applied to CustomTkinter controls

### Requirement: Common UI text uses readable fonts
The application SHALL use a shared readable font definition for common labels, buttons, entries, option menus, switches, checkboxes, and value labels across the main UI.

#### Scenario: Common controls are readable
- **WHEN** the main tabs and right-side configuration panels are displayed
- **THEN** common controls SHALL use the shared comfort font size instead of the previous small 12-point baseline

### Requirement: Long-form text areas use editor-sized fonts
The application SHALL use a shared editor font definition for long-form text boxes used for chapter content, logs, architecture, directory, character state, summaries, chapter viewing, previews, and generated text review.

#### Scenario: Writing areas are easier to read
- **WHEN** the user edits or reviews long-form generated novel content
- **THEN** the text area SHALL render with an editor-sized font larger than the common control font

### Requirement: Layout remains usable after scaling
The application SHALL preserve the current major layout while preventing comfort-level scaling from causing obvious overlap or unusable clipping in primary workflows.

#### Scenario: Main screen remains usable
- **WHEN** the user opens the main functions screen after the comfort scaling change
- **THEN** the left editing area, step buttons, log area, and right configuration/parameter area SHALL remain visible and usable without obvious text overlap

### Requirement: Styling constants are centralized
The application SHALL define comfort scaling and core font tuples in one shared UI style location used by UI construction modules.

#### Scenario: Font size can be adjusted centrally
- **WHEN** a future maintainer needs to tune the comfort font size
- **THEN** the primary common and editor font sizes SHALL be adjustable from the shared UI style location rather than requiring edits to every tab module
