# headless-reference — shipd-ask delta

## ADDED Requirements

### Requirement: The headless contract has one reference
id: headless-contract-reference

`plugins/s/skills/ask/references/headless.md` SHALL hold the no-human contract
as its single source, beside `oracle-contract.md`, with one stable `##`
heading per part: `Codebase first` (answer what the repository settles and ask
nothing about it), `Oracle next` (run `oracle-lookup` judged per
`oracle-contract.md`, adopt an authoritative `ANSWER` as given, and record it
`**Answered by:** ORACLE`), `Default last` (on `INSUFFICIENT`, an advisory
answer, a failed lookup, or no verdict, adopt the recommended default and
record an entry with `**Verdict:** INSUFFICIENT`, `**Answered by:**
ASSUMPTION`, the options in `**Question:**` with the default first, the
adopted default in a non-empty `**Answer:**`, and `**Queued:**` when the oracle
filed one), and `Never a dialog` (no question round, no AskUserQuestion). `Default last`
records the entry only when the session writes or revises a plan; otherwise,
such as a build coordinator answering a sub-agent `QUESTION:`, it answers with
the default and records nothing. Every
inline copy of this contract SHALL point at the file instead of restating it:
the autopilot skill's plan, build, and re-plan instructions, the autopilot
driver's prompts, and the epic-grill planner instruction. The epic-grill
instruction SHALL keep its `PLANNER` label as an explicit override of `Default
last`, because its final round asks a human. The file SHALL pass the docs lint.

#### Scenario: The reference carries the four parts by heading
- **WHEN** `headless.md` is inspected
- **THEN** it has the `##` headings `Codebase first`, `Oracle next`, `Default
  last`, and `Never a dialog`, and `Default last` names `ASSUMPTION`

#### Scenario: No copy tells a driven session to record its default as USER
- **WHEN** the autopilot skill and the driver's prompts are searched for the
  headless instruction
- **THEN** each points at `headless.md` and none tells the session to record
  its own default as `**Answered by:** USER`

#### Scenario: Epic-grill keeps its provisional label
- **WHEN** the epic-grill planner instruction is read
- **THEN** it points at `headless.md` and states that it records `PLANNER`
  instead of `ASSUMPTION`

