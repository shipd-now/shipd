## ADDED Requirements

### Requirement: Live modal artifacts
id: modal-live-artifacts

While the spec-detail modal shows the empty-artifacts notice for a member
whose live heartbeat entry carries a stage, the notice SHALL name the
in-flight stage and attempt (e.g. `plan in progress (plan#1) — spec files
appear once emitted`) instead of the idle "not yet planned" text; a member
with no live stage SHALL keep the existing idle notice. While the notice is
showing, the modal SHALL re-resolve the member's artifacts on its refresh
interval and, when artifacts appear, SHALL replace the notice with the tabbed
artifact view without the modal being closed and reopened.

#### Scenario: A driving member's notice names its stage
- **WHEN** the modal opens for a member with no artifacts whose heartbeat
  entry shows stage `plan`, attempt 1
- **THEN** the notice reads that a plan stage is in progress (`plan#1`)
  rather than "not yet planned"

#### Scenario: An idle member keeps the idle notice
- **WHEN** the modal opens for a member with no artifacts and no live stage
- **THEN** the notice is the existing "not yet planned — no spec files" text

#### Scenario: Artifacts appear without reopening
- **WHEN** the modal is open showing the notice and the member's artifact set
  is written to its location
- **THEN** a subsequent refresh tick replaces the notice with the
  Plan/Spec/Tasks tabs on the same open screen

#### Scenario: Mounted tabs are left alone
- **WHEN** the modal already shows artifact tabs
- **THEN** refresh ticks do not remount or reset them
