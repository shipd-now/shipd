## MODIFIED Requirements

### Requirement: Every PR-opening flow calls the skill
id: pr-callers
base: 7ae0ef723b90

No file under `plugins/s` outside test directories, and not `AGENTS.md`, SHALL contain `gh pr create --fill`. The build ship phase (auto, draft, and epic-close), `worktree.sh` next steps, `/s:gate` fallbacks, `/s:epic` amend, `/s:initiative` set, the autopilot build prompt, and the harness build and gate bodies SHALL direct the agent to open the pull request with `/s:pr`, passing `--draft` in draft mode. The skill SHALL be registered in the `AGENTS.md` skill sentence and `docs/cheatsheet.md`, with a harness body `bodies/pr.md`.

#### Scenario: No bare fill remains
- **WHEN** the pr skill test searches `plugins/s` (excluding tests) and `AGENTS.md` for `gh pr create --fill`
- **THEN** it finds none

#### Scenario: Draft mode passes the flag
- **WHEN** the test reads the build skill's draft-mode section
- **THEN** it finds `/s:pr --draft`

#### Scenario: Registrations and body render
- **WHEN** the test reads `AGENTS.md` and `docs/cheatsheet.md` and renders the `pr` body
- **THEN** each contains `/s:pr` and the render succeeds
