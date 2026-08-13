## ADDED Requirements

### Requirement: Modal chrome containment
id: modal-chrome-containment

Every modal chrome element — badge chips, title text, and every button — of
the board's modal screens (spec-detail, epic-detail, epic-run confirmation,
and graph config) SHALL render fully inside its screen's container with a
nonzero region: badge chips SHALL size to their text (plus padding), never
stretching to the row width or pushing sibling chips outside the modal, so a
member with risk, lane, live stage, and epic renders all of its chips
visibly. While the accent title bar's ✕ close control is focused, it SHALL
keep the accent bar's color scheme (the dimmed-accent treatment) rather than
the theme's default focused-button styling. The test suite SHALL carry a
reusable chrome-containment sweep exercised against all four modal screens,
so a chrome element rendering outside its container fails CI.

#### Scenario: All badge chips are visible and sized to content
- **WHEN** the spec-detail modal opens for a member with a risk, a derived
  lane, a live stage, and an epic
- **THEN** all four chips render inside the modal container, each sized to
  its text plus padding, none stretched to the row width

#### Scenario: Epic modal chips are contained
- **WHEN** the epic-detail modal opens for an epic with members
- **THEN** its badge row chips and every member row's lane chip render
  inside the modal container

#### Scenario: The focused close control keeps the accent scheme
- **WHEN** a modal opens and its ✕ close control holds focus
- **THEN** the control's background is the dimmed accent, not the theme's
  default focused-button color

#### Scenario: The containment sweep guards all modal screens
- **WHEN** the chrome-containment sweep runs against the spec-detail,
  epic-detail, run-confirmation, and graph config screens
- **THEN** it asserts every button, badge chip, and title text region sits
  inside the screen's container with nonzero width, and fails on any
  violation
