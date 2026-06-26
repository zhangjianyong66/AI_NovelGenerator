## Purpose

Define frontend management of project configuration, model settings, embedding settings, proxy settings, and generation stage model selection.

## Requirements

### Requirement: Project output path management
The system SHALL allow the frontend to load, display, select, and persist the active project output path used by existing novel files.

#### Scenario: User opens project settings
- **WHEN** the project or settings page loads with a connected backend
- **THEN** the frontend displays the current output path from persisted configuration or project state

#### Scenario: User changes output path
- **WHEN** the user selects or enters a valid output path and saves it
- **THEN** the backend persists the path in the same configuration boundary used by existing generation workflows

### Requirement: Novel parameter editing
The system SHALL allow the frontend to edit and save the novel parameters currently available in the Python GUI.

#### Scenario: User edits core novel parameters
- **WHEN** the user changes topic, genre, chapter count, per-chapter word count, chapter number, user guidance, involved characters, key items, scene location, or time constraint
- **THEN** the backend saves those values for subsequent generation operations

#### Scenario: User reloads saved parameters
- **WHEN** the frontend is reopened after parameters were saved
- **THEN** the saved values are loaded instead of reverting to mock defaults

### Requirement: LLM configuration management
The system SHALL allow the frontend to manage multiple LLM configurations with the same functional coverage as the current GUI.

#### Scenario: User manages LLM configs
- **WHEN** the user creates, renames, deletes, selects, or saves an LLM configuration
- **THEN** the backend persists the updated configuration set without exposing unrelated secrets in the response

#### Scenario: User tests LLM config
- **WHEN** the user requests a test for the selected LLM configuration
- **THEN** the backend performs the test and returns success or failure details for frontend display

### Requirement: Embedding and proxy configuration
The system SHALL allow the frontend to edit, save, and test Embedding configuration and proxy configuration.

#### Scenario: User tests Embedding config
- **WHEN** the user requests an Embedding configuration test
- **THEN** the backend runs an embedding query test and returns success or failure details

#### Scenario: User changes proxy settings
- **WHEN** the user enables or disables proxy settings and saves
- **THEN** the backend persists the proxy setting and applies the expected environment behavior for subsequent operations

### Requirement: Generation stage model selection
The system SHALL allow the frontend to select which saved LLM configuration is used by each generation stage.

#### Scenario: User assigns generation configs
- **WHEN** the user selects configurations for architecture, directory, draft, finalization, consistency review, or prompt draft
- **THEN** the backend persists the stage-to-configuration mapping

#### Scenario: Missing selected config
- **WHEN** a saved stage mapping references a deleted LLM configuration
- **THEN** the frontend displays a recoverable invalid-selection state and requires the user to choose an available configuration before running that stage
