## CHANGED Requirements

### Requirement: Enforce SSO session timeout
id: enforce-sso-timeout
base: 000000000000

The system SHALL end an SSO session after 15 minutes of inactivity and MUST
require re-authentication before granting further access.

#### Scenario: Idle session is ended
- **WHEN** an SSO session has seen no activity for 15 minutes
- **THEN** the session is invalidated and the next request is redirected to
  re-authenticate
