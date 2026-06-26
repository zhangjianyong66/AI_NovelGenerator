## MODIFIED Requirements

### Requirement: Service errors are normalized
The system SHALL normalize local backend errors into user-facing error state and developer-facing diagnostic detail, and SHALL expose those states through consistent frontend status patterns.

#### Scenario: Backend returns validation error
- **WHEN** a local backend request fails because input is invalid
- **THEN** the frontend displays a concise validation message near the related operation

#### Scenario: Backend request fails unexpectedly
- **WHEN** a local backend request fails due to connection loss or server error
- **THEN** the frontend records diagnostic detail and shows a recoverable error state without breaking navigation

#### Scenario: Page operation succeeds
- **WHEN** a save, import, test, backup, restore, generation creation, or role update operation succeeds
- **THEN** the frontend displays a consistent success state near the related operation without requiring every page to implement a custom message style

#### Scenario: Page operation is loading
- **WHEN** a page region is loading data or submitting an operation through the service bridge
- **THEN** the frontend displays a consistent loading state and prevents duplicate conflicting submissions for that region
