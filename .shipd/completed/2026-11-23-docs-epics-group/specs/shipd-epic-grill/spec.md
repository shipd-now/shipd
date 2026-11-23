## ADDED Requirements

### Requirement: Epic grill user documentation
id: epic-grill-user-docs

The repository SHALL provide `docs/epic-grill.md`, the main page for
`/s:epic-grill`, titled "Epic grill". The page SHALL conform to the shipd
documentation standard with `<!-- doc-type: how-to -->` as its first line,
and SHALL open by saying what the grill is, then hold exactly three level-2
sections in this order: `## When to use it`, `## How to run it`, and
`## Reference`.

The page SHALL state:

- that the grill plans every unplanned member of one approved epic, asks
  every human decision in one final round, and gates the plans together;
- that it needs an epic at `ready` or `active`, and plans nothing for a
  `draft` epic;
- that it selects members in the `unplanned` lane plus members left at
  `draft` by an interrupted grill, so a second run resumes the first;
- the run as numbered steps: preflight and member order, planning in waves,
  the consistency pass across plans, the final round with a reply such as
  `1a 2b` and the recommended default listed first, the amend and gate step,
  the risk report, and the launch preflight;
- that member order follows the epic's `After` column when it holds a
  dependency, and a judged dependency order otherwise;
- that a member reaches `ready` only through the gate;
- that the grill never builds, never opens a pull request, and never edits
  the epic, and that an answer binding every member is flagged for
  `/s:epic <epic> amend`;
- that a green launch preflight ends on the hand-off `/s:autopilot <epic>`,
  a red one lists the failing checks and hands off nothing, and a member
  scored `medium` or `high` draws a `/s:plan-deep` suggestion.

The `## Reference` section SHALL hold one table covering the `<epic>`
argument and the `--parallel N` flag with its default of 3 members per plan
wave. The page SHALL link `epics.md` and `autopilot.md`, and SHALL carry no
mermaid fence. Every command on the page SHALL be a `/s:` skill or a `shipd`
verb.

#### Scenario: Page covers the one-round contract
- **WHEN** `docs/epic-grill.md` is inspected
- **THEN** it states that every decision is asked in one final round after
  the consistency pass, with the recommended default first

#### Scenario: Page covers selection and resume
- **WHEN** `docs/epic-grill.md` is inspected
- **THEN** it names the `ready` or `active` epic precondition, the
  `unplanned` and `draft` member selection, and that a re-run resumes

#### Scenario: Page covers the hand-off
- **WHEN** the run steps are read to their end
- **THEN** they name the gate as the only path to `ready`, the launch
  preflight, and `/s:autopilot <epic>` as the hand-off on a green preflight

#### Scenario: Page passes the lint and its links resolve
- **WHEN** `docs_lint.py` runs over `docs/epic-grill.md`
- **THEN** it exits 0 with the file marked `how-to`, the file holds no
  mermaid fence and no engine script path, and every relative link resolves
