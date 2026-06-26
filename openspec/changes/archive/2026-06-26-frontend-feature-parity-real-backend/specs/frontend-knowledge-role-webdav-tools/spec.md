## ADDED Requirements

### Requirement: Knowledge files can be imported
The system SHALL allow the frontend to import knowledge files into the active project's vectorstore through the backend.

#### Scenario: User imports knowledge file
- **WHEN** the user selects a supported knowledge file and confirms import
- **THEN** the backend imports the file into the active output path vectorstore and returns import status for frontend display

#### Scenario: Knowledge import fails
- **WHEN** import fails because the file is invalid, the output path is missing, or embedding configuration fails
- **THEN** the frontend displays the failure reason and does not report the vectorstore as updated

### Requirement: Vectorstore can be cleared
The system SHALL allow the frontend to clear the active project's vectorstore with explicit confirmation.

#### Scenario: User confirms vectorstore clear
- **WHEN** the user confirms clearing the vectorstore for the active output path
- **THEN** the backend removes the vectorstore data and the frontend reports the result

#### Scenario: User cancels vectorstore clear
- **WHEN** the user cancels the confirmation
- **THEN** the backend is not called to clear vectorstore data

### Requirement: Plot arcs can be viewed
The system SHALL allow the frontend to display plot arc information generated in the active output directory.

#### Scenario: User opens plot arcs
- **WHEN** `plot_arcs.txt` exists in the active output path
- **THEN** the frontend displays its content in a readable view

#### Scenario: Plot arcs are missing
- **WHEN** `plot_arcs.txt` does not exist
- **THEN** the frontend shows an empty or missing-state message without crashing

### Requirement: Role library supports basic management
The system SHALL provide frontend access to basic role library operations backed by the existing role library file structure.

#### Scenario: User views roles
- **WHEN** a project has a role library directory
- **THEN** the frontend displays categories and role files available under that library

#### Scenario: User edits role content
- **WHEN** the user edits and saves a role
- **THEN** the backend writes the role content to the correct role file while preserving the existing library format

#### Scenario: User selects roles for chapter parameters
- **WHEN** the user selects one or more roles from the role library
- **THEN** the selected role names can be applied to the chapter involved-characters parameter

### Requirement: WebDAV backup and restore are available
The system SHALL allow the frontend to test WebDAV connection, back up local configuration, and restore local configuration through the backend.

#### Scenario: User tests WebDAV connection
- **WHEN** the user submits WebDAV URL, username, and password for testing
- **THEN** the backend tests the connection and returns success or failure without exposing the password back to the frontend

#### Scenario: User backs up config
- **WHEN** the user requests WebDAV backup with valid settings
- **THEN** the backend uploads the local configuration to the configured remote location and reports the result

#### Scenario: User restores config
- **WHEN** the user confirms WebDAV restore
- **THEN** the backend creates a local backup before replacing configuration and the frontend refreshes configuration state after restore
