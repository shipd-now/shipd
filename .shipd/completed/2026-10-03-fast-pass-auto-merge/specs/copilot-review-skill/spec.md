## ADDED Requirements

### Requirement: Fast-pass marker and workflow arming
id: fast-pass-workflow-arming

The Copilot code-review skill template at `integrations/copilot/SKILL.md`
SHALL instruct the reviewing agent to emit the line
`<!-- shipd-fast-pass: eligible -->` directly above the verdict marker, and
only where the reviewed pull request carries a completed shipd change
directory whose every delta scenario the agent judged met. The template SHALL
state that the verdict marker remains the body's last line, so the fast-pass
line never displaces it and the gate's backwards verdict scan — which breaks on
the first verdict marker it meets — classifies exactly as before.

The review-gate workflow template at
`integrations/copilot/copilot-review-gate.yml` SHALL read the repository
Actions variable `SHIPD_FAST_PASS` from `vars` in the step environment, the way
it already reads `SHIPD_GATE_FAIL_OPEN`, and SHALL arm auto-merge with
`gh pr merge --auto --squash --delete-branch` only where **all** of these hold:
the variable reads exactly `true`; the classified state is `success`; that
state came from a matched `ship-it` verdict marker rather than from the
marker-less fail-open path; and the reviewed body carries the fast-pass line,
found by the same whole-line equality scan bounded to the final 200 lines. The
arming SHALL run after the commit status is posted, and SHALL log which
condition was unmet where it does not run.

If the arming call fails, then the workflow SHALL log the failure and SHALL NOT
fail the job — the posted status is the gate, and a refused merge arming is not
a broken review. The poll fallback SHALL never arm the fast-pass, because
GitHub's own reviewer authors no shipd marker and so can satisfy neither the
verdict nor the fast-pass condition.

#### Scenario: The template pins the fast-pass line above the verdict
- **WHEN** `plugins/s/integrations/copilot/SKILL.md` is read
- **THEN** it names `<!-- shipd-fast-pass: eligible -->`, places it directly
  above the verdict marker, and states the verdict marker is still the last
  line

#### Scenario: An eligible reviewed body arms the merge
- **GIVEN** `SHIPD_FAST_PASS` reads `true`
- **WHEN** the workflow classifies a body whose matched verdict marker is
  `ship-it` and which carries the fast-pass line
- **THEN** it posts `success` and runs `gh pr merge --auto --squash
  --delete-branch`

#### Scenario: A fail-open pass arms nothing
- **GIVEN** `SHIPD_FAST_PASS` reads `true` and `SHIPD_GATE_FAIL_OPEN` is unset
- **WHEN** the workflow classifies a body carrying no verdict marker and posts
  `success` fail-open
- **THEN** no merge arming is run and the step logs that no verdict marker was
  matched

#### Scenario: An unset variable arms nothing
- **GIVEN** `SHIPD_FAST_PASS` is unset
- **WHEN** the workflow classifies a `ship-it` body carrying the fast-pass line
- **THEN** no merge arming is run

#### Scenario: A failed arming does not fail the job
- **WHEN** the merge arming call exits non-zero
- **THEN** the workflow logs the failure and the job's exit code is unchanged
