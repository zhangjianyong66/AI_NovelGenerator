## MODIFIED Requirements

### Requirement: Supported generation stages are available
The system SHALL provide frontend operations for architecture generation, directory generation, draft generation, finalization, batch generation, and consistency review, organized in a stable task creation panel.

#### Scenario: User views generation actions
- **WHEN** the generation page or workspace action bar is displayed
- **THEN** actions for architecture, directory, draft, finalization, batch generation, and consistency review are available when backend prerequisites are satisfied

#### Scenario: Prerequisite is missing
- **WHEN** a generation action requires missing output path, missing model config, missing chapter number, or missing source file
- **THEN** the frontend disables or blocks the action with a specific prerequisite message

#### Scenario: Generation page has stable operation panels
- **WHEN** the user opens the generation page
- **THEN** task creation, batch parameters, task list, and selected task details or logs are presented as distinct regions

### Requirement: Job status and logs are visible
The system SHALL show generation job status, progress, logs, errors, and result references in the frontend, with task scanning separated from detailed log viewing.

#### Scenario: Job is running
- **WHEN** a generation job is running
- **THEN** the frontend displays running status, latest progress, and log lines from the backend

#### Scenario: Job fails
- **WHEN** a generation job fails
- **THEN** the frontend displays failed status, error message, and any available logs without marking output files as successfully updated

#### Scenario: Job succeeds
- **WHEN** a generation job succeeds
- **THEN** the frontend refreshes affected project files, chapters, summaries, or task lists from the backend

#### Scenario: User scans jobs before reading logs
- **WHEN** multiple generation jobs exist
- **THEN** the task list shows concise job status and progress, and detailed logs are shown in a selected task detail area rather than expanded for every job by default

### Requirement: Batch generation is controllable
The system SHALL allow batch generation parameters to be provided from the frontend and tracked as a backend job, using a dedicated batch parameter area instead of an ad hoc inline form.

#### Scenario: User starts batch generation
- **WHEN** the user provides start chapter, end chapter, target words, minimum words, and auto-enrich option
- **THEN** the backend creates a batch job and the frontend tracks per-chapter progress or aggregate progress

#### Scenario: User cancels batch dialog
- **WHEN** the user cancels the batch generation dialog before submitting
- **THEN** no backend generation job is created

#### Scenario: Batch parameters remain visible while preparing
- **WHEN** the user is preparing a batch generation job
- **THEN** the batch chapter range, target words, minimum words, and auto-enrich option are shown together in one dedicated parameter region
