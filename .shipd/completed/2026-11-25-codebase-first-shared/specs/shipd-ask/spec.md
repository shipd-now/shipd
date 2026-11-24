# codebase-first-shared — shipd-ask delta

## MODIFIED Requirements

### Requirement: The headless contract has one reference
id: headless-contract-reference
base: b9ba2c93921e

`plugins/s/skills/ask/references/headless.md` SHALL hold the no-human contract
as its single source, beside `oracle-contract.md`, with one stable `##`
heading per part: `Codebase first` (answer what the repository and the request
settle, read the verified capabilities, in-flight changes, epic, code and
request before treating anything as open, and ask nothing a read could have
answered; it binds interactive sessions too and `/s:plan` loads it), `Oracle
next` (run `oracle-lookup` judged per
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

#### Scenario: Codebase first is the shared rule
- **WHEN** the `Codebase first` part is read
- **THEN** it says the rule binds interactive sessions too, that `/s:plan` loads it, and that a question reading could have answered is a failure, in prose with no code fence or plugin-root variable

#### Scenario: No copy tells a driven session to record its default as USER
- **WHEN** the autopilot skill and the driver's prompts are searched for the
  headless instruction
- **THEN** each points at `headless.md` and none tells the session to record
  its own default as `**Answered by:** USER`

#### Scenario: Epic-grill keeps its provisional label
- **WHEN** the epic-grill planner instruction is read
- **THEN** it points at `headless.md` and states that it records `PLANNER`
  instead of `ASSUMPTION`
