## ADDED Requirements

### Requirement: Runnable premises are verified before emission
id: verified-runnable-premises

Where a plan asserts how an **existing** command, script, or flag behaves, and a
task or delta requirement depends on that assertion, the planner SHALL verify it
by running that command before emitting, and SHALL cite what was observed — the
invocation and its output or exit code — rather than a pointer to the
implementation's source. Assertions about behavior the change itself will create,
and assertions no task depends on, SHALL NOT require verification.

#### Scenario: A relied-on claim about an existing command is run
- **GIVEN** a plan whose task list depends on an existing script exiting zero on
  a second invocation
- **WHEN** the planner reaches emission
- **THEN** that script has been run and the plan cites the invocation and the
  observed exit code

#### Scenario: Reading the source is not verification
- **GIVEN** a plan asserting an existing command's behavior, supported only by a
  citation of that command's implementation
- **WHEN** the readiness attestation is checked
- **THEN** the premise counts as unverified

#### Scenario: Claims about not-yet-written behavior are exempt
- **GIVEN** a plan describing how the component this change will create should
  behave
- **WHEN** the planner reaches emission
- **THEN** no verification run is required for that description

#### Scenario: A premise no task depends on is exempt
- **GIVEN** a plan mentioning an existing command's behavior in passing, with no
  task or delta requirement depending on it
- **WHEN** the planner reaches emission
- **THEN** no verification run is required for that mention

### Requirement: Premise evidence appears in the readiness attestation
id: premise-evidence-in-attestation

The readiness checklist SHALL carry the runnable-premise rule as evidence under
its affected-capabilities-and-files item rather than as an additional checklist
item, so the four items are unchanged in number. The attestation SHALL name each
verified premise with its observation.

#### Scenario: The checklist keeps four items
- **WHEN** the readiness checklist is read after this change
- **THEN** it still gates on exactly four items

#### Scenario: The attestation carries the observation
- **GIVEN** a plan that verified a runnable premise
- **WHEN** its readiness attestation is printed
- **THEN** the attestation names the premise and what running it showed
