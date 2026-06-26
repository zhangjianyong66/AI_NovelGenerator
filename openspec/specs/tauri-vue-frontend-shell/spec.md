## Purpose

Specify the standalone Tauri + Vue + TypeScript frontend shell and its development workflow.

## Requirements

### Requirement: Frontend project shell
The system SHALL provide a standalone Tauri + Vue + TypeScript frontend project that can coexist with the existing Python `customtkinter` GUI.

#### Scenario: Frontend shell is present
- **WHEN** a developer inspects the repository after this change
- **THEN** the repository contains a dedicated frontend project directory with Vue, Vite, TypeScript, and Tauri configuration files

#### Scenario: Existing GUI remains available
- **WHEN** a developer runs the existing Python desktop entry point
- **THEN** the current `customtkinter` GUI remains the active production GUI and is not replaced by the new frontend shell

### Requirement: Frontend routing and application layout
The system SHALL provide frontend routing and a shared application shell for navigating between major UI areas.

#### Scenario: User navigates major sections
- **WHEN** the frontend runs in development mode
- **THEN** the UI exposes navigable sections for projects, workspace, chapters, generation, settings, and knowledge management

### Requirement: Frontend state and service boundaries
The system SHALL define frontend-side state stores, service modules, and TypeScript types without calling real Python backend services.

#### Scenario: Pages load without backend service
- **WHEN** the frontend starts without a Python API server
- **THEN** pages render using mock service data instead of failing due to unavailable backend services

#### Scenario: Business logic remains out of frontend
- **WHEN** frontend service and store files are reviewed
- **THEN** they contain UI state and mock data access only, not novel generation, model invocation, vectorstore, or config persistence logic

### Requirement: Independent frontend developer workflow
The system SHALL document and expose development commands for the new frontend without changing existing Python setup commands.

#### Scenario: Developer starts new frontend
- **WHEN** a developer follows the frontend setup instructions
- **THEN** the Tauri + Vue frontend can be installed and started independently of `python main.py`

#### Scenario: Python workflow is unchanged
- **WHEN** a developer follows the existing Python run command
- **THEN** `python main.py` remains the command for starting the current GUI
