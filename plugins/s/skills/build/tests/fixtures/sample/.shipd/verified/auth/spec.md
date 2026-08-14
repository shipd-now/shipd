# auth

### Requirement: Enforce SSO session timeout
id: enforce-sso-timeout

The system SHALL end an SSO session after 30 minutes of inactivity and MUST
require re-authentication before granting further access.

#### Scenario: Idle session is ended
- **WHEN** an SSO session has seen no activity for 30 minutes
- **THEN** the session is invalidated and the next request is redirected to
  re-authenticate

### Requirement: Legacy cookie fallback
id: legacy-cookie-fallback

The system SHALL accept a legacy session cookie when no SSO token is present.

#### Scenario: Legacy cookie accepted
- **WHEN** a request carries a legacy cookie and no SSO token
- **THEN** the existing session is honored

### Requirement: Password complexity
id: password-complexity

The system SHALL require account passwords to be at least 12 characters long.

#### Scenario: Short password is rejected
- **WHEN** a user sets an 8-character password
- **THEN** the system rejects it and explains the minimum length
