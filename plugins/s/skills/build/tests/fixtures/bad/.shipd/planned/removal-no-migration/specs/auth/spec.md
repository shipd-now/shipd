## REMOVED Requirements

### Requirement: Legacy cookie fallback
id: legacy-cookie-fallback
base: 000000000000
Reason: The legacy cookie auth path is retired.

#### Scenario: Legacy cookie accepted
- **WHEN** a request carries a legacy cookie and no SSO token
- **THEN** the existing session is honored
