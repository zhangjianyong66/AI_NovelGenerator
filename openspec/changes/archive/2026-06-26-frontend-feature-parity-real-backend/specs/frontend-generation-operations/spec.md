## ADDED Requirements

### Requirement: Generation operations create backend jobs
The system SHALL let the frontend start generation operations by creating backend jobs instead of running generation logic in the browser.

#### Scenario: User starts architecture generation
- **WHEN** the user starts novel architecture generation from the frontend
- **THEN** the frontend sends the current project parameters to the backend and receives a generation job identifier

#### Scenario: User starts chapter draft generation
- **WHEN** the user starts chapter draft generation from the frontend
- **THEN** the backend job uses the selected chapter number, chapter context, saved model selection, and active output path

### Requirement: Supported generation stages are available
The system SHALL provide frontend operations for architecture generation, directory generation, draft generation, finalization, batch generation, and consistency review.

#### Scenario: User views generation actions
- **WHEN** the generation page or workspace action bar is displayed
- **THEN** actions for architecture, directory, draft, finalization, batch generation, and consistency review are available when backend prerequisites are satisfied

#### Scenario: Prerequisite is missing
- **WHEN** a generation action requires missing output path, missing model config, missing chapter number, or missing source file
- **THEN** the frontend disables or blocks the action with a specific prerequisite message

### Requirement: Job status and logs are visible
The system SHALL show generation job status, progress, logs, errors, and result references in the frontend.

#### Scenario: Job is running
- **WHEN** a generation job is running
- **THEN** the frontend displays running status, latest progress, and log lines from the backend

#### Scenario: Job fails
- **WHEN** a generation job fails
- **THEN** the frontend displays failed status, error message, and any available logs without marking output files as successfully updated

#### Scenario: Job succeeds
- **WHEN** a generation job succeeds
- **THEN** the frontend refreshes affected project files, chapters, summaries, or task lists from the backend

### Requirement: Batch generation is controllable
The system SHALL allow batch generation parameters to be provided from the frontend and tracked as a backend job.

#### Scenario: User starts batch generation
- **WHEN** the user provides start chapter, end chapter, target words, minimum words, and auto-enrich option
- **THEN** the backend creates a batch job and the frontend tracks per-chapter progress or aggregate progress

#### Scenario: User cancels batch dialog
- **WHEN** the user cancels the batch generation dialog before submitting
- **THEN** no backend generation job is created
