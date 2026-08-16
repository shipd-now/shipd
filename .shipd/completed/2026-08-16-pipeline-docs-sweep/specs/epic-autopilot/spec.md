## MODIFIED Requirements

### Requirement: Attempt-budget failure handling
id: three-strike-parking
base: 78864b825c78

When a driven stage fails for a non-gate reason — session error or timeout,
grade unmet after the resume budget, or a non-zero replacement or custom
command — the autopilot SHALL re-drive that stage with the failure summary
appended to the prompt, up to that entry's fresh-attempt budget: the entry's
`autopilot.attempts` when declared, else three. A stage still failing after
its final attempt SHALL park the member as `needs-human`, recording the
stage, the reason, and the most recent session id so a human can reopen the
exact conversation with `claude --resume <id>`; the member's worktree SHALL
be left intact and the run SHALL continue with the next member.

#### Scenario: Second attempt can succeed
- **GIVEN** a stage that fails once and succeeds on re-drive under the
  default budget
- **WHEN** the autopilot drives it
- **THEN** the member proceeds and no parking occurs

#### Scenario: Final failure parks with the session id
- **WHEN** a stage fails every attempt of its budget
- **THEN** the member is parked as needs-human with stage, reason, and
  session id, its worktree remains, and the next member starts
