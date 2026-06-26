## MODIFIED Requirements

### Requirement: Project output path management
The system SHALL allow the frontend to load, display, select, and persist the active project output path used by existing novel files, and SHALL present this setting in a clearly grouped project-parameter configuration area.

#### Scenario: User opens project settings
- **WHEN** the project or settings page loads with a connected backend
- **THEN** the frontend displays the current output path from persisted configuration or project state

#### Scenario: User changes output path
- **WHEN** the user selects or enters a valid output path and saves it
- **THEN** the backend persists the path in the same configuration boundary used by existing generation workflows

#### Scenario: User navigates settings groups
- **WHEN** the user opens the settings page
- **THEN** project parameters, LLM configuration, Embedding configuration, proxy and generation-stage model mapping, and WebDAV settings are separated into tabs or equivalent grouped sections

### Requirement: LLM configuration management
The system SHALL allow the frontend to manage multiple LLM configurations with the same functional coverage as the current GUI, while keeping dense model fields inside a focused LLM settings group.

#### Scenario: User manages LLM configs
- **WHEN** the user creates, renames, deletes, selects, or saves an LLM configuration
- **THEN** the backend persists the updated configuration set without exposing unrelated secrets in the response

#### Scenario: User tests LLM config
- **WHEN** the user requests a test for the selected LLM configuration
- **THEN** the backend performs the test and returns success or failure details for frontend display

#### Scenario: LLM settings are visually grouped
- **WHEN** the user edits LLM provider, Base URL, model name, API key, temperature, max tokens, timeout, or interface format
- **THEN** those controls appear in a focused LLM configuration group rather than being visually mixed with unrelated WebDAV or project parameter fields

### Requirement: Embedding and proxy configuration
The system SHALL allow the frontend to edit, save, and test Embedding configuration and proxy configuration, and SHALL present Embedding and proxy controls in clearly separated settings groups.

#### Scenario: User tests Embedding config
- **WHEN** the user requests an Embedding configuration test
- **THEN** the backend runs an embedding query test and returns success or failure details

#### Scenario: User changes proxy settings
- **WHEN** the user enables or disables proxy settings and saves
- **THEN** the backend persists the proxy setting and applies the expected environment behavior for subsequent operations

#### Scenario: Embedding warning is visible
- **WHEN** the user views or changes the active Embedding configuration
- **THEN** the UI displays a clear reminder that changing real Embedding models may require clearing the existing vectorstore
