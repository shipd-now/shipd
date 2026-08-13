## ADDED Requirements

### Requirement: Rate-limit login attempts

The system SHALL reject more than five failed login attempts from one IP within
a rolling 60-second window.

#### Scenario: Sixth attempt is rejected
- **WHEN** a client makes a sixth failed login within 60 seconds
- **THEN** the request is refused with a 429 response
