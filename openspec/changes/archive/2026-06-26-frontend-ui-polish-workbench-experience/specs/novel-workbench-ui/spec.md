## MODIFIED Requirements

### Requirement: Workbench information architecture
The system SHALL provide a workbench-oriented UI structure for novel generation instead of directly mirroring the existing tab-only layout, and SHALL make the main flow from project selection to workspace, chapter editing, generation, knowledge management, and settings clear in navigation and page composition.

#### Scenario: Workbench layout shows core regions
- **WHEN** the frontend workspace page is opened
- **THEN** the UI presents a navigation region, a central work area, and a context area for generation state or parameters

#### Scenario: Main navigation follows the writing flow
- **WHEN** the application shell displays the primary navigation
- **THEN** the navigation order and labels make project, workspace, chapters, generation, knowledge, and settings available as distinct workflow steps

#### Scenario: Workspace summarizes current focus
- **WHEN** the workspace page is opened with an active project
- **THEN** the page summarizes the active project, current chapter focus, core file status, and next generation actions without duplicating every detailed tool from other pages

### Requirement: Shared UI patterns support workbench pages
The system SHALL provide reusable frontend UI components or component patterns for common page headers, action areas, form sections, status messages, confirmation areas, list selection, and long-form text editing.

#### Scenario: Page headers are consistent
- **WHEN** a user opens project, workspace, chapters, generation, knowledge, or settings pages
- **THEN** the page title, supporting text, and primary actions use a consistent header pattern

#### Scenario: Long text editing is consistent
- **WHEN** a user edits or views novel settings, directory content, chapter content, plot arcs, role content, logs, or summaries
- **THEN** the UI uses a consistent long-text area pattern with appropriate read-only/editing state and word count where relevant

#### Scenario: Empty and loading states are consistent
- **WHEN** a page region has no tasks, no chapters, no knowledge files, no plot arcs, no roles, or is loading data
- **THEN** the UI displays a consistent empty or loading state instead of leaving the area visually ambiguous
