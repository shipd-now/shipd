## MODIFIED Requirements

### Requirement: Adversarial validation gates verified
id: adversarial-validation-gates-verified
base: 00d24ccf73ae

When the task list is complete and the test suite passes, build SHALL spawn an
independent validator sub-agent — on the same tier as the execution
sub-agents, using the `s:validator` agent type whose definition carries the
validator's full role contract — that reads the change's delta specs, the
relevant masters, and the code, and attempts to refute each `#### Scenario:`
by exercising the real behavior. The validator's spawn message SHALL carry
only the change name; it SHALL receive neither the builders' summaries nor the
orchestrator's conversation. The build SHALL NOT set the status to `verified`
while any scenario verdict is `refuted`; a refutation returns the build to the
fix loop before validation runs again.

#### Scenario: Validator runs before verified
- **WHEN** all tasks are done and the suite is green
- **THEN** an `s:validator` sub-agent reports a per-scenario verdict, and
  only a fully confirmed report allows `set-status verified`

#### Scenario: Refutation blocks the merge
- **WHEN** the validator refutes a scenario with evidence
- **THEN** the orchestrator routes the finding through the fix loop and
  re-validates; the change is not merged in the meantime

#### Scenario: Validator is isolated from the builders
- **WHEN** the validator sub-agent is spawned
- **THEN** its spawn message carries the change name only — no builder
  summaries and no orchestrator history — and its role contract comes from
  the `s:validator` definition
