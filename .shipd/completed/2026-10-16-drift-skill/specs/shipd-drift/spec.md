## ADDED Requirements

### Requirement: Drift skill runs the verb and judges only flagged members
id: drift-skill-run

`/s:drift <change> | --epic <slug> [--base <ref>] [--json]` SHALL run
`spec_status.py drift` with the same change, `--epic`, and `--base`
arguments it was given, relay the verb's text output verbatim, and branch on
the verb's exit code alone: on `0` it SHALL report every member as clean or
skipped and SHALL read no plan and no diff; on `4` it SHALL judge exactly the
members whose `findings` array is non-empty; on `1` or `2` it SHALL relay the
engine's `Error:` or usage text and stop with no verdict. The skill SHALL be
read-only — it writes no file, runs no mutating engine verb, no `git fetch`,
no re-plan, and no gate — and SHALL never open a question dialog or spawn an
agent.

#### Scenario: A clean epic runs no model
- **GIVEN** an epic whose `drift --epic <slug>` exits 0
- **WHEN** `/s:drift --epic <slug>` runs
- **THEN** the report lists every measured member under `clean:` and every
  skipped member under `skipped:`, no `cat change` or `git diff` is read, and
  no verdict line is printed

#### Scenario: Only flagged members are judged
- **GIVEN** an epic whose verb output has one member with findings, one
  clean member, and one skipped member
- **WHEN** `/s:drift --epic <slug>` runs
- **THEN** exactly one verdict line is printed, naming the flagged member,
  and the clean and skipped members appear only on the `clean:` and
  `skipped:` lines

#### Scenario: A verb error is relayed, not judged
- **WHEN** `/s:drift <change>` runs and the verb exits 1
- **THEN** the skill prints the verb's `Error:` line, prints no verdict, and
  stops

#### Scenario: The session mutates nothing
- **WHEN** an `/s:drift` invocation completes
- **THEN** no file under the repository was created or edited and no
  `git fetch`, status, gate, or emit command ran

### Requirement: Evidence is bounded to the plan and finding-scoped diffs
id: drift-skill-evidence

For each flagged member the skill SHALL read only: the member's artifacts
through `spec_status.py --root <root> cat change <member>` (the `root` the
verb reported), the epic's Decisions through `cat epic <slug>` once per run,
and per finding — for `file-drift`, `git -C <root> diff
<planned_at>..<base.sha> -- <path>` (when that diff exceeds 400 lines, the
path's `git log --format='%h %s'` plus the hunks naming an identifier the
plan cites); for `symbol-gone`, the diff over the paths `git grep -l -w -F
<symbol> <planned_at>` lists and `git log --format='%h %s' -S<symbol>` over
the same range; for `stale-base`, the current master requirement through
`cat verified <capability>`. The skill SHALL NOT read other repository
files or a whole-tree diff.

#### Scenario: File drift evidence is the cited path's diff
- **GIVEN** a flagged member with one `file-drift src/engine.py` finding
- **WHEN** the skill gathers evidence
- **THEN** it reads the member's `cat change` output and `git diff
  <planned_at>..<base.sha> -- src/engine.py`, and nothing else from the tree

#### Scenario: Symbol evidence follows the symbol's files
- **GIVEN** a flagged member with a `symbol-gone old_helper` finding
- **WHEN** the skill gathers evidence
- **THEN** it diffs the paths `git grep -l -w -F old_helper <planned_at>`
  listed, with the `<sha>:` prefix stripped

### Requirement: One verdict per flagged member
id: drift-skill-verdicts

The skill SHALL return exactly one of `holds`, `revise`, or `conflict` per
flagged member: `holds` when no assumption the plan's Implementation, tasks,
or delta scenarios make about the drifted paths, symbols, or master changed;
`revise` when an assumption broke and a revision within the plan's
`**Answered by:** USER` ledger entries and the epic's Decisions repairs it;
`conflict` when the repair or the drift itself contradicts a `USER` entry or
an epic Decision, naming the `Q<n>` or the Decision. `PLANNER` and `ORACLE`
ledger entries SHALL NOT raise `conflict`. If the evidence cannot show that an
assumption still holds, then the verdict SHALL be `revise`, never `holds`.
The report SHALL end with a `## Drift verdicts` block holding, in the verb's
member order, one line `<member>: <verdict> — <reason>` per flagged member
(`revise` lines append `; revise: <what>`, `conflict` lines append
`; contradicts: Q<n> | Decision "<name>"`), then `clean: <members>`,
`skipped: <member> (<reason>)` lines, and the tally `verdicts: <n> holds,
<n> revise, <n> conflict; <n> clean, <n> skipped`.

#### Scenario: Shifted line citations hold
- **GIVEN** a flagged member whose only drift is a commit adding lines above
  a `path:line` the plan cites, leaving the cited symbols intact
- **WHEN** the skill judges it
- **THEN** the verdict line reads `<member>: holds — ...`

#### Scenario: A removed called symbol is revise
- **GIVEN** a flagged member whose tasks call a `symbol-gone` symbol and
  whose ledger holds no `USER` entry about it
- **WHEN** the skill judges it
- **THEN** the verdict is `revise` and the line names the tasks or sections
  to change after `revise:`

#### Scenario: Drift against a user answer is conflict
- **GIVEN** a flagged member whose `USER`-answered `Q2` fixes an interface
  that the diff removed from `main`
- **WHEN** the skill judges it
- **THEN** the verdict is `conflict` and the line ends `contradicts: Q2`

#### Scenario: The tally closes the block
- **WHEN** an epic run judges two members `holds` and one `revise` with two
  clean members and one skipped
- **THEN** the block's last line is `verdicts: 2 holds, 1 revise, 0
  conflict; 2 clean, 1 skipped`

### Requirement: JSON mode is one object
id: drift-skill-json

Where the invocation carries `--json`, the skill SHALL run only the verb's
`--json` form and emit a single JSON object and nothing else — no fence, no
prose — with `mode` (`epic` or `change`), `epic`, `change`, `base`
(`ref`, `sha`), `verdicts` (per flagged member: `member`, `root`,
`planned_at`, `verdict`, `reason`, `contradicts`, `revise`, and the verb's
`findings` verbatim), `clean`, `skipped` (`member`, `reason`), and `error`
(`null`, or the engine's error line when the verb exited 1 or 2, with every
array empty).

#### Scenario: JSON carries verdicts and clean members
- **WHEN** `/s:drift --epic <slug> --json` runs on an epic with one flagged
  and one clean member
- **THEN** the response parses as one object whose `verdicts` has one entry
  with `verdict` in `holds|revise|conflict` and whose `clean` names the
  other member

#### Scenario: A verb error is still well-formed JSON
- **WHEN** `/s:drift nosuch --json` runs and the verb exits 1
- **THEN** the response is one object with `error` set to the engine's line
  and empty `verdicts`, `clean`, and `skipped`

### Requirement: Skill registration
id: drift-skill-registration

The plugin SHALL ship `plugins/s/skills/drift/SKILL.md` (frontmatter
`name: drift`, trigger phrases `"drift"`, `"check drift"`, `"has the plan
drifted"`, `"/s:drift"`, claimed by no other skill), an ungated body template
`plugins/s/harness/bodies/drift.md` opening with a description marker and
containing none of `subagent`, `sub-agent`, or `AskUserQuestion`, a `/s:drift`
row in `README.md`'s Orchestration table and in `docs/cheatsheet.md`'s command
table and Unattended group, a mention in `AGENTS.md`'s skill roll, a
shipped-text contract test, and a `plugin.json` version bump.

#### Scenario: Body parity and token rules pass
- **WHEN** `test_harness_bodies` runs
- **THEN** the body ids still equal the `SKILL.md`-bearing skill directories,
  and `drift` rendered with no features carries no forbidden token

#### Scenario: The contract test pins the vocabulary
- **WHEN** `test_drift_skill_contract` runs
- **THEN** it asserts the skill and body name the verb, `--epic`, `--base`,
  `--json`, all three verdicts, the `## Drift verdicts` block, the
  `verdicts:` tally, and that `/s:drift` appears in the three registry files
