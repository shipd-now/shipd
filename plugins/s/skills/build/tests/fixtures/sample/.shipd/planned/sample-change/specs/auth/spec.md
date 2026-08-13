## ADDED Requirements

### Requirement: Rate-limit login attempts
id: rate-limit-login

The system SHALL reject more than five failed login attempts from one IP within
a rolling 60-second window.

#### Scenario: Sixth attempt is rejected
- **WHEN** a client makes a sixth failed login within 60 seconds
- **THEN** the request is refused with a 429 response

## MODIFIED Requirements

### Requirement: Enforce SSO session timeout
id: enforce-sso-timeout
base: 3c1af58513af

The system SHALL end an SSO session after 15 minutes of inactivity and MUST
require re-authentication before granting further access.

#### Scenario: Idle session is ended
- **WHEN** an SSO session has seen no activity for 15 minutes
- **THEN** the session is invalidated and the next request is redirected to
  re-authenticate

## REMOVED Requirements

### Requirement: Legacy cookie fallback
id: legacy-cookie-fallback
base: 990d30a4f1b3
Reason: The legacy cookie auth path is retired.
Migration: All clients use SSO tokens as of release 3.0; no action required.

## RENAMED Requirements

- FROM: password-complexity
  TO: password-strength
