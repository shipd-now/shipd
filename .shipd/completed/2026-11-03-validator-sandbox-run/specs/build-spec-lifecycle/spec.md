## MODIFIED Requirements

### Requirement: Adversarial validation gates verified
id: adversarial-validation-gates-verified
base: 8dde8af7dd1d

When the task list is complete and the test suite passes, build SHALL spawn an
independent validator sub-agent — on the same tier as the execution
sub-agents, using the `s:validator` agent type whose definition carries the
validator's full role contract — that reads the change's delta specs, the
relevant masters, the code, and, when `plan.md` names a design scratch directory,
that directory as a read-only reference, and attempts to refute each
`#### Scenario:` by exercising the real behavior. The validator's spawn message
SHALL carry only the change name and the absolute path of `sandbox-run.sh`; it SHALL receive neither the builders'
summaries nor the orchestrator's conversation. The build SHALL NOT set the status
to `verified` while any scenario verdict is `refuted`; a refutation returns the
build to the fix loop before validation runs again. Where the resolved
pipeline's `build` entry declares `validator` false, build SHALL NOT spawn
the validator sub-agent, and passing mechanical verification (all tasks
complete, the suite green, the spec re-linting clean) alone SHALL allow
`set-status verified`.

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
- **THEN** its spawn message carries the change name and the sandbox wrapper path only — no builder
  summaries and no orchestrator history — and its role contract comes from
  the `s:validator` definition

#### Scenario: Validator exercises design fidelity against the design
- **WHEN** a change carries a design and its delta specs include design-fidelity
  scenarios
- **THEN** the validator reads the plan-named design scratch directory and
  refutes or confirms those scenarios against the real design

#### Scenario: Pipeline validator opt-out skips the gate
- **GIVEN** a resolved build entry declaring `validator` false
- **WHEN** all tasks are done, the suite is green, and the spec re-lints
  clean
- **THEN** no `s:validator` sub-agent is spawned and the status advances
  to `verified` on mechanical verification alone
