## ADDED Requirements

### Requirement: Plan user documentation
id: plan-user-docs

The repository SHALL provide `docs/plan.md`, titled "Plan a change", as the
main page for `/s:plan`, `/s:plan-deep`, `/s:status`, and the change
lifecycle, conforming to the shipd documentation standard with the marker
`how-to` on its first line and a total line count within that type's cap.

The page SHALL follow the main-page shape: opening paragraphs saying what
planning produces, then `## When to use it`, `## How to run it`, and a
closing `## Reference`, in that order.

The opening and `## When to use it` SHALL cover: the change as a lean
artifact set (`plan.md`, a delta spec per affected capability, `tasks.md`)
under the content directory's `planned/<change>/`, written in the change's
worktree; that `/s:plan` stops before any code is written; and when to reach
for `/s:plan`, for `/s:plan-deep`, and for `/s:epic` instead.

`## How to run it` SHALL cover, for `/s:plan`: the invocation; investigation
before any question; the personal memory and oracle consultation before a
person is asked, linking `docs/oracle.md`; the single typed question round;
the fast and depth paths; the readiness attestation; the install at `draft`;
the context gate's promotion to `ready` or parking at `rejected`; re-running
`/s:plan <change>` to enrich a rejected change; the recording, bundle-slug,
and supplied-document inputs, linking `docs/video-ingest.md`; and the
`/s:build` hand-off. For `/s:plan-deep` it SHALL cover: both invocation forms
(`<change>`, and `<epic> [<member> ...]`); the statuses it walks (`draft`,
`ready`, `rejected`); the risk-ordered walk of an epic's medium and high
members; the in-place edit and re-gate; and both endings.

`## Reference` SHALL hold: a table of the six statuses (`draft`, `ready`,
`active`, `complete`, `verified`, `rejected`) with their meanings; the guard
rules on transitions; `/s:status` as the way to report or change a status;
a table of the `shipd status`, `shipd lint`, `shipd list`, and `shipd locate`
verbs; and a link to the content directory's `README.md` for the requirement
and delta grammar, which the page SHALL NOT restate.

Every interactive command on the page SHALL invoke the `shipd` binary or name
a `/s:` skill — never an engine script path.

#### Scenario: Page follows the main-page shape
- **WHEN** the level-2 headings of `docs/plan.md` are listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: Page covers planning
- **WHEN** `docs/plan.md` is inspected
- **THEN** it names the three artifacts, the investigate-first rule, the
  oracle consultation, the single question round, the gate's `ready` and
  `rejected` outcomes, the enrichment re-run, and the `/s:build` hand-off

#### Scenario: Page covers the deep walk
- **WHEN** the `/s:plan-deep` prose is read
- **THEN** it gives both invocation forms, the three statuses the skill
  walks, the in-place edit, and the re-gate

#### Scenario: Reference holds the lifecycle
- **WHEN** the page's `## Reference` section is read
- **THEN** it lists all six statuses with meanings, the transition guards,
  `/s:status`, the four `shipd` verbs, and a resolving link to
  `../.shipd/README.md`

#### Scenario: Page passes the lint
- **WHEN** `docs_lint.py` runs over `docs/plan.md`
- **THEN** it exits 0 with the page marked `how-to`, and the page names no
  `spec_status.py`, `spec_emit.py`, or `spec_gate.py` path
