## ADDED Requirements

### Requirement: Workbench information architecture
The system SHALL provide a workbench-oriented UI structure for novel generation instead of directly mirroring the existing tab-only layout.

#### Scenario: Workbench layout shows core regions
- **WHEN** the frontend workspace page is opened
- **THEN** the UI presents a navigation region, a central work area, and a context area for generation state or parameters

### Requirement: Project and chapter navigation model
The system SHALL represent projects and chapters as first-class navigation concepts in the new UI.

#### Scenario: User views project entry points
- **WHEN** the projects page is opened
- **THEN** the UI displays project-oriented entry points using mock project data

#### Scenario: User views chapter entry points
- **WHEN** the chapter editor or workspace page is opened
- **THEN** the UI displays chapter-oriented navigation or selection using mock chapter data

### Requirement: Generation task visibility
The system SHALL provide UI regions for generation actions, task status, and logs using mock task data.

#### Scenario: User reviews task status
- **WHEN** the generation page or workspace context panel is opened
- **THEN** the UI displays mock generation tasks with status information

#### Scenario: User sees generation action affordances
- **WHEN** the workspace page is opened
- **THEN** the UI exposes affordances for architecture, directory, draft, finalization, and batch generation without invoking real backend generation

### Requirement: Settings and knowledge management placeholders
The system SHALL provide page placeholders for model settings, embedding settings, proxy settings, role library, and knowledge management.

#### Scenario: User navigates settings
- **WHEN** the settings page is opened
- **THEN** the UI presents model, embedding, and proxy setting sections using mock configuration data

#### Scenario: User navigates knowledge management
- **WHEN** the knowledge page is opened
- **THEN** the UI presents knowledge and role library areas as placeholders for future integration
