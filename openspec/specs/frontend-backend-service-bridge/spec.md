## Purpose

Define how the Vue frontend accesses real local backend services while retaining a controlled mock fallback.

## Requirements

### Requirement: Frontend uses a single service bridge
The system SHALL route frontend data access through a dedicated service bridge instead of calling `mockApi` directly from pages or stores.

#### Scenario: Page loads data through service bridge
- **WHEN** a frontend page loads projects, chapters, configuration, jobs, or knowledge data
- **THEN** the page obtains the data through the service bridge API rather than importing `mockApi` directly

#### Scenario: Store actions use service bridge
- **WHEN** a Pinia store loads or mutates application data
- **THEN** the store delegates the operation to the service bridge and does not hard-code mock data access

### Requirement: Backend health and mode are visible
The system SHALL expose the current frontend data mode as connected backend, disconnected backend, or mock fallback.

#### Scenario: Backend is reachable
- **WHEN** the frontend health check succeeds against the local backend
- **THEN** the application shell displays a connected backend state and enables real write operations

#### Scenario: Backend is unavailable
- **WHEN** the frontend health check fails and mock fallback is active
- **THEN** the application shell displays mock fallback state and real write operations are blocked or clearly marked as non-persistent

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

### Requirement: Frontend business logic remains out of Vue
The system SHALL keep generation, model invocation, vectorstore manipulation, config persistence, WebDAV protocol work, and role analysis logic outside Vue components.

#### Scenario: Frontend generation action is reviewed
- **WHEN** a developer reviews frontend page and store files for generation operations
- **THEN** those files create service requests and update UI state but do not invoke LLM adapters or implement generation algorithms

#### Scenario: Frontend knowledge action is reviewed
- **WHEN** a developer reviews frontend knowledge and role pages
- **THEN** those files call backend services but do not implement vector splitting, embedding, or WebDAV transfer logic
