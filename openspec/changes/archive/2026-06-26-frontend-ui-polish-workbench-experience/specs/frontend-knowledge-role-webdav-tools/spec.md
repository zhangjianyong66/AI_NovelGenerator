## MODIFIED Requirements

### Requirement: Knowledge files can be imported
The system SHALL allow the frontend to import knowledge files into the active project's vectorstore through the backend, and SHALL place knowledge-file operations in a dedicated knowledge files tab or equivalent section.

#### Scenario: User imports knowledge file
- **WHEN** the user selects a supported knowledge file and confirms import
- **THEN** the backend imports the file into the active output path vectorstore and returns import status for frontend display

#### Scenario: Knowledge import fails
- **WHEN** import fails because the file is invalid, the output path is missing, or embedding configuration fails
- **THEN** the frontend displays the failure reason and does not report the vectorstore as updated

#### Scenario: User opens knowledge files tab
- **WHEN** the user opens the knowledge files area
- **THEN** import controls, vectorstore clear controls, known file list, loading state, and operation result messages are shown without mixing in role editing controls

### Requirement: Vectorstore can be cleared
The system SHALL allow the frontend to clear the active project's vectorstore with explicit confirmation using a consistent confirmation UI pattern.

#### Scenario: User confirms vectorstore clear
- **WHEN** the user confirms clearing the vectorstore for the active output path
- **THEN** the backend removes the vectorstore data and the frontend reports the result

#### Scenario: User cancels vectorstore clear
- **WHEN** the user cancels the confirmation
- **THEN** the backend is not called to clear vectorstore data

#### Scenario: Clear action uses consistent confirmation
- **WHEN** the user initiates vectorstore clearing
- **THEN** the UI presents the same confirmation pattern used by other destructive or overwriting frontend actions

### Requirement: Plot arcs can be viewed
The system SHALL allow the frontend to display plot arc information generated in the active output directory, in a dedicated plot arcs tab or equivalent section.

#### Scenario: User opens plot arcs
- **WHEN** `plot_arcs.txt` exists in the active output path
- **THEN** the frontend displays its content in a readable view

#### Scenario: Plot arcs are missing
- **WHEN** `plot_arcs.txt` does not exist
- **THEN** the frontend shows an empty or missing-state message without crashing

#### Scenario: Plot arcs are separated from role editing
- **WHEN** the user reads plot arcs
- **THEN** the content is displayed in a focused long-text viewer without role library editing controls in the same content region

### Requirement: Role library supports basic management
The system SHALL provide frontend access to basic role library operations backed by the existing role library file structure, in a dedicated role library tab or equivalent section.

#### Scenario: User views roles
- **WHEN** a project has a role library directory
- **THEN** the frontend displays categories and role files available under that library

#### Scenario: User edits role content
- **WHEN** the user edits and saves a role
- **THEN** the backend writes the role content to the correct role file while preserving the existing library format

#### Scenario: User selects roles for chapter parameters
- **WHEN** the user selects one or more roles from the role library
- **THEN** the selected role names can be applied to the chapter involved-characters parameter

#### Scenario: Role editing is separated from knowledge import
- **WHEN** the user opens the role library area
- **THEN** role category navigation, role selection, role content editing, import, and apply-to-chapter actions are grouped together without knowledge file import controls in the same content region
