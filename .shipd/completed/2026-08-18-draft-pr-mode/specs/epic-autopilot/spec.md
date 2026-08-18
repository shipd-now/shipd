## MODIFIED Requirements

### Requirement: Pipeline-honoring stage execution
id: pipeline-stage-execution
base: 7930db3ad338

Per member, the autopilot SHALL execute the resolved
`autonomous-pipeline` entries in order, covering the `plan`, `gate`,
`build`, and `review` registry stages and any `custom` entries, while
noting and ignoring `research` and `epic` entries as pre-approval stages.
A skipped entry SHALL be skipped; a replaced entry SHALL run its
replacement command in the member's worktree instead of the built-in
behavior; a `tools` binding SHALL be surfaced to the driven session as
prompt guidance including its fallback. Built-in behavior: `plan` drives a
headless `/s:plan <member>` graded on a lint-clean member change at
`Status: ready`; `gate` runs the gate engine, where a context rejection
(exit 2) triggers the single oracle-backed enrichment attempt (see
oracle-gate-enrichment) and the member parks as `rejected` only when that
attempt does not end in a gate pass; `build` drives a headless `/s:build`
graded on the change archived under `completed/` and
a PR existing for the member branch — where the resolved configuration
declares `pr-mode: draft` (shipd-config pr-mode-key), the build stage's
driving prompt SHALL name the draft-PR ship (a draft PR, no auto-merge
arming) rather than an auto-merging PR; `review` drives a headless
review-post-and-disposition session — its prompt naming the disposition
loop (implement or reply, then resolve) — graded on the head SHA's
`semantic-review` status being `success` **and** the gate's
`resolve --check` reporting zero unresolved threads. Member worktrees
SHALL be created with the plugin's worktree helper. If a member's
worktree no longer exists when a stage starts or after a stage failure —
a driven session may legitimately remove it while shipping the member —
then the autopilot SHALL resolve the member's outcome from the
repository root via the member branch's pull request: a merged PR SHALL
record the member `shipped` with its PR URL and skip the remaining
stages; otherwise the member SHALL park as `needs-human` with a
worktree-vanished reason and the most recent session id — regardless of
the resolved `pr-mode`, since a draft-mode build leaves its worktree in
place and a vanished one stays an anomaly. In both cases
the run SHALL continue with the next member.

When the pipeline instead completes with the member's worktree still
present, the autopilot SHALL resolve the member's outcome from its PR: a
merged PR SHALL record the member `shipped` with its URL. Where the
resolved configuration declares `pr-mode: draft`, a PR that exists but has
not merged SHALL record the member `drafted` with its PR URL — the
expected terminal state of a draft-mode ship, never parked — while a
member with no PR at all SHALL still park as needs-human at stage `merge`.
Under the default `auto` mode, a PR that exists but has not merged SHALL
park the member as needs-human at stage `merge` with the PR URL and the
most recent session id — never recorded `shipped` — because the driven
build waits for its own PR to merge before returning (build-spec-lifecycle
ship-changes-as-prs), so an unmerged PR at drive end signals a stalled or
timed-out ship rather than a success. In every case the run SHALL continue
with the next member.

#### Scenario: Full pass ships a member
- **GIVEN** a member whose plan gates clean and whose build succeeds
- **WHEN** the autopilot drives it
- **THEN** its worktree came from the plugin helper, the change is
  archived, and an auto-merging PR exists for its branch

#### Scenario: Gate rejection parks only after the enrichment attempt
- **WHEN** the gate exits 2 on a member's plan and the oracle-backed
  enrichment attempt does not end in a gate pass
- **THEN** the member is parked as rejected, no re-drive occurs, and the
  run continues with the next member

#### Scenario: Review grade requires disposition, not just green
- **GIVEN** a green `semantic-review` status but one unresolved
  gate-authored thread
- **WHEN** the review stage is graded
- **THEN** the grade does not pass until `resolve --check` reports
  `unresolved=0`

#### Scenario: Skipped gate is honored
- **GIVEN** a resolved pipeline whose gate entry carries skip
- **WHEN** a member is driven
- **THEN** no gate runs between plan and build for that member

#### Scenario: Custom step runs at its position
- **GIVEN** a custom entry between build and review
- **WHEN** a member is driven
- **THEN** the custom command runs in the member's worktree after build

#### Scenario: Present worktree with an unmerged PR parks the member
- **GIVEN** the default `auto` pr-mode and a member whose pipeline
  completes with its worktree present but whose PR has not merged
- **WHEN** the autopilot resolves the member's outcome
- **THEN** the member parks as needs-human at stage `merge` with the PR URL
  and the most recent session id, is not recorded `shipped`, and the run
  continues with the next member

#### Scenario: Draft mode records a drafted member
- **GIVEN** `pr-mode: draft` resolved and a member whose pipeline
  completes with its worktree present and an open unmerged PR
- **WHEN** the autopilot resolves the member's outcome
- **THEN** the member is recorded `drafted` with its PR URL, is not
  parked, and the run continues with the next member

#### Scenario: Vanished worktree with a merged PR records an early ship
- **GIVEN** a build stage whose driven session merged the member's PR and
  removed the member's worktree
- **WHEN** the autopilot's next turn or stage finds the worktree missing
- **THEN** the member is recorded `shipped` with its PR URL, no further
  stages run for it, and the next member is driven

#### Scenario: Vanished worktree without a merged PR parks the member
- **GIVEN** a member whose worktree disappears mid-run while its PR is
  absent or unmerged
- **WHEN** the autopilot resolves the member's outcome
- **THEN** the member parks as needs-human with a worktree-vanished
  reason and the most recent session id, and the run continues

### Requirement: Run report and controls
id: run-report-and-controls
base: 58d5f8578df6

The autopilot SHALL accept `--max-members`, `--dry-run`, `--timeout`, and
`--max-resumes`; `--dry-run` SHALL print the member order and the
resolved pipeline and drive nothing. Every run SHALL end with a report
listing shipped members with PR URLs, drafted members with their draft PR
URLs (draft-mode runs), parked members split into rejected
and needs-human — needs-human entries with their session ids, rejected
entries with the enrichment session id when an enrichment session ran —
skipped members with their states, and members unreached due to
`--max-members`; the report SHALL be written machine-readably and
summarized for humans, the summary printing a `claude --resume` pointer
for any parked member whose entry carries a session id. If a parked
entry carries no session id, then the summary SHALL omit the resume
pointer entirely rather than print a null value. When at least one
member PR merged during the run, the autopilot SHALL finish with the
epic-sync close-out in a fresh worktree, invoking the status CLI with a
well-formed invocation (the root option before the subcommand) so the
derivation actually runs; drafted members SHALL NOT trigger the
close-out — it runs only on an actual merge. When the close-out
derivation succeeds and
leaves the close-out worktree unchanged, the autopilot SHALL remove that
worktree and its branch; when it wrote a status change, the summary
SHALL name the worktree path so a human can ship it.

#### Scenario: Dry run drives nothing
- **WHEN** a run executes with `--dry-run`
- **THEN** the member order and resolved pipeline print and no session,
  gate, or worktree action occurs

#### Scenario: Report accounts for every member
- **GIVEN** a run with one shipped, one rejected (whose enrichment session
  ran), one needs-human, and one unreached member
- **WHEN** the run ends
- **THEN** the report lists each under its outcome, with a PR URL for
  the shipped member and a session id for both the needs-human and the
  rejected member

#### Scenario: Drafted members are reported distinctly and trigger no close-out
- **GIVEN** a draft-mode run where every driven member ends with an open
  draft PR
- **WHEN** the run ends
- **THEN** the report lists each member under `drafted` with its PR URL,
  the summary renders a `drafted:` line per member, and no epic-sync
  close-out runs

#### Scenario: Parked without a session omits the pointer
- **WHEN** the summary renders a needs-human member whose entry has no
  session id (parked before any session started)
- **THEN** the line carries the member, stage, and reason but no
  `claude --resume` fragment

#### Scenario: Close-out derivation runs
- **WHEN** the close-out invokes the status CLI in the fresh worktree
- **THEN** the invocation is accepted and the derived epic status is
  relayed in the run output

#### Scenario: No-op close-out cleans up
- **WHEN** the close-out sync exits zero without writing a status change
- **THEN** the close-out worktree and its branch are removed

#### Scenario: Written close-out is handed to a human
- **WHEN** the close-out sync writes a changed epic status
- **THEN** the summary names the close-out worktree path for a human to
  ship
