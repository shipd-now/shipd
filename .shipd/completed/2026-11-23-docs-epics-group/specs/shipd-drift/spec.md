## ADDED Requirements

### Requirement: Drift user documentation
id: drift-user-docs

The repository SHALL provide `docs/drift.md`, the main page for `/s:drift`,
titled "Drift". The page SHALL conform to the shipd documentation standard
with `<!-- doc-type: how-to -->` as its first line, and SHALL open by saying what drift is, then hold exactly three level-2
sections in this order: `## When to use it`, `## How to run it`, and
`## Reference`.

The page SHALL state:

- that a gated plan cites files, symbols, and master requirements, and that
  `main` moves between the gate and the build;
- that the engine measures which citations moved, and that `/s:drift` judges
  whether each move breaks the plan;
- that the skill is read-only: it edits no file, re-plans nothing, and sets
  no status;
- the two invocations, `/s:drift <change>` and `/s:drift --epic <slug>`,
  with the optional `--base <ref>` and `--json`;
- the run as numbered steps, ending on the `## Drift verdicts` block, shown
  in one example fence with a `holds`, a `revise`, and a `conflict` line and
  the closing tally;
- the next step per verdict: `revise` means revise the plan and gate it
  again, and `conflict` means a human decides on the named `Q<n>` or epic
  Decision;
- that only an entry answered by the user, or an epic Decision, raises
  `conflict`;
- that autopilot runs the same check before each member's build.

The `## Reference` section SHALL hold a table of the three verdicts `holds`,
`revise`, and `conflict` with the two non-verdict states `clean` and
`skipped`, and a table of the three finding kinds `file-drift`,
`symbol-gone`, and `stale-base`, each with its meaning. The page SHALL link
`autopilot.md`, `epics.md`, and `supersession-gate.md` as the owner of the
check that build runs at its start, and SHALL carry no mermaid fence. Every
command on the page SHALL be a `/s:` skill or a `shipd` verb.

#### Scenario: Page separates measuring from judging
- **WHEN** `docs/drift.md` is inspected
- **THEN** it states that the engine measures what moved, that the skill
  judges it, and that the skill is read-only

#### Scenario: Page shows the verdict block
- **WHEN** `docs/drift.md` is inspected
- **THEN** it holds one example `## Drift verdicts` block with `holds`,
  `revise`, and `conflict` lines, and names the next step for `revise` and
  for `conflict`

#### Scenario: Reference tables cover verdicts and findings
- **WHEN** the `## Reference` section is read
- **THEN** it defines `holds`, `revise`, `conflict`, `clean`, `skipped`,
  `file-drift`, `symbol-gone`, and `stale-base`

#### Scenario: Page passes the lint and its links resolve
- **WHEN** `docs_lint.py` runs over `docs/drift.md`
- **THEN** it exits 0 with the file marked `how-to`, the file holds no
  mermaid fence and no engine script path, and every relative link resolves
