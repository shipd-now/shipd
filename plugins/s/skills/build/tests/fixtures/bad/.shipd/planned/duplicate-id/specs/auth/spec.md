## ADDED Requirements

### Requirement: Rate-limit login attempts
id: rate-limit-login

The system SHALL reject more than five failed login attempts from one IP within
a rolling 60-second window.

#### Scenario: Sixth attempt is rejected
- **WHEN** a client makes a sixth failed login within 60 seconds
- **THEN** the request is refused with a 429 response

### Requirement: Rate-limit login attempts again
id: rate-limit-login

The system SHALL also reject more than fifty failed attempts per hour.

#### Scenario: Hourly cap is enforced
- **WHEN** a client exceeds fifty failed logins in one hour
- **THEN** the account is locked for review
