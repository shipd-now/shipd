# epic-grill
Status: verified

## Idea

Add `/s:epic-grill`, which plans every unplanned epic member through
`/s:plan` in dependency order, asks the human every open decision in one
final round, then reconciles and gates the plans together.

### Motivation

Someone delivering an epic must run `/s:plan` member by member and answer its
questions one member at a time, while `/s:autopilot` plans unattended and never
asks the human. Nobody can plan a whole epic in one pass and confirm the plans
agree with each other and with the epic's Decisions.

### Details

- New skill `plugins/s/skills/epic-grill/SKILL.md`: preflight, dependency
  order, one deferring `/s:plan` sub-agent per member, a cross-plan
  consistency pass, one final AskUserQuestion round, amend, gate, hand off.
- Ledger value `PLANNER` marks a default a planner adopted while the human
  question waits for the final round.
- `spec_gate.py` gains a provisional-entry check: a `PLANNER` entry rejects
  the change.
- Registration: harness body, `AGENTS.md`, `README.md`,
  `docs/cheatsheet.md`, plugin version.

Affected capabilities: `shipd-epic-grill` (new), `context-gate` and
`shipd-spec-format` (modified).

### Non-goals

- No change to `/s:plan`, `/s:autopilot`, or their specs.
- No building, shipping, or PR creation for members; the grill hands off to
  `/s:autopilot`.
- No edit to the epic file; epic-wide answers are flagged for
  `/s:epic <epic> amend`.
- No linter rule on the `**Answered by:**` value.

## Implementation

- **Contract home.** The deferral rule lives in the grill's spawn instruction,
  pinned by `epic-grill-planner-contract`; `/s:plan` stays untouched (user,
  Q1). This follows `/s:autopilot`'s plan-stage instruction. Rejected: a
  named mode inside `/s:plan`.
- **Gate timing.** Planners stop at `draft`; the grill gates every member after
  the final round (user, Q2). An interrupted run leaves only `draft` members,
  which `/s:autopilot` skips, so no unconfirmed default gets built. A re-run of
  the grill resumes them: it selects `draft` members and reads their `PLANNER`
  entries from disk.
- **Provisional record.** A deferred decision is a normal ledger entry with
  `**Answered by:** PLANNER`, holding the adopted default; the gate rejects it
  (user, Q3). Running `spec_gate.py` alone on such a draft parks it at
  `rejected`, where `/s:plan` enrichment puts the entry to the user.
- **Gate check.** Add `_check_provisional_entries(root, change)` to
  `plugins/s/skills/build/scripts/spec_gate.py`, called last in
  `collect_findings`. It reads the plan's `## Questions and answers` section
  with `spec_lint._section_lines` and `spec_lint.QA_ENTRY_RE`, and emits
  `ledger entry Q<n> is provisional (**Answered by:** PLANNER) and awaits a
  human answer` per matching entry. The match is the regex
  `^\s*-\s*\*\*Answered by:\*\*\s*PLANNER\b`. Add the check to the module
  docstring after the four context checks.
- **Separate requirement.** The check is a new `context-gate` requirement,
  `provisional-entry-check`, not an edit to `context-sufficiency-checks`. A
  MODIFIED delta must restate that requirement's literal marker list, and the
  gate's own placeholder scan rejects any delta that carries it. Rejected:
  rewording the master's marker list to dodge the scan.
- **Skill shape.** Model on `plugins/s/skills/autopilot/SKILL.md`: version
  banner from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`, every
  command from the repo root. Member states come from
  `epic-show <epic> --json` lanes. A `draft` member's worktree root comes from
  `locate <member>`. Planning runs one member at a time, so each planner reads
  earlier plans.
- **Planner instruction.** Give the instruction verbatim in the skill:

  ```
  Run /s:plan for the change `<member>`, a member of the epic `<epic>`,
  planned by /s:epic-grill. No human is available during this run.
  Members already planned in this run (read each with
  `spec_status.py --root <root> cat change <slug>`; keep names, interfaces,
  and shared decisions consistent with them): <slug>: <root>, ...
  Consult the oracle as /s:plan prescribes, but open no question round. For
  every decision the oracle leaves open (INSUFFICIENT, an advisory ANSWER, or
  no verdict), adopt your recommended default as a settled decision and record
  a `## Questions and answers` entry with `**Answered by:** PLANNER`: the
  options in `**Question:**` with the default first, the default in
  `**Answer:**`, and `**Queued:**` when the oracle filed one.
  Install the change through spec_emit.py and stop at Status: draft. Do not
  run spec_gate.py; /s:epic-grill gates every member after its final round.
  End your turn with `DEFERRED:` and one line per PLANNER entry
  (`Q<n> | <summary> | <options, default first>`), or `DEFERRED: none`.
  ```
- **Agenda source.** Build the agenda from the on-disk `PLANNER` entries, not
  the `DEFERRED:` blocks, so a resumed run and a run where a sub-agent was
  cut off read the same agenda.
- **Dialogs.** AskUserQuestion allows at most 4 questions per call. Context
  rides in each question and option text, because the harness can drop prose
  that shares a turn with a dialog. A rejected dialog follows `/s:plan`'s
  question-rejection recovery.
- **Harness body.** `plugins/s/harness/bodies/epic-grill.md` carries no `if:`
  gates and so needs no reference file. For a bare harness it plans members in
  turn within the session and asks the agenda as one numbered typed round. It
  must not contain the tokens `subagent`, `sub-agent`, or `AskUserQuestion`.

Risk: two members modifying the same master requirement both base on today's
hash, so the later one goes stale once the first ships. The consistency pass
names such pairs in the hand-off, and the build-time gate catches the stale
base through enrichment.

## Questions and answers

### Q1: Where does the deferral contract live?
- **Question:** Grill spawn instruction pinned in the grill's own spec, or a
  named mode in `/s:plan`'s skill and spec? Recommendation: the grill's spec.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** In the grill's spawn instruction, pinned as requirements in the
  `shipd-epic-grill` spec; `/s:plan` stays untouched.
- **Queued:** q-epic-grill-deferred-question-contract-home

### Q2: When do members pass the gate?
- **Question:** Planners stop at `draft` and the grill gates after the final
  round, or planners gate as usual and the grill re-gates? Recommendation:
  gate after the final round.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Planners stop at `draft`; the grill gates every member only after
  the final round and its amendments.
- **Queued:** q-epic-grill-member-gate-timing

### Q3: How is a deferred decision recorded?
- **Question:** A `PLANNER` ledger entry plus a gate check, the entry without
  a check, or session memory only? Recommendation: entry plus gate check.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** A ledger entry with `**Answered by:** PLANNER`, rewritten to
  `USER` after the human answers; the gate rejects any remaining one.
- **Queued:** q-epic-grill-deferred-decision-record

## Readiness attestation

### Problem and motivation

Epic members are planned and questioned one at a time by hand, or planned
with no human at all by `/s:autopilot`.

Evidence:

- `plugins/s/skills/epic/SKILL.md:446-451` hands off one `/s:plan` per member.
- Requirement `oracle-aware-driven-sessions` (`epic-autopilot`) has driven
  planners self-recommend and never wait for a human.

### Scope and non-goals

A new skill, one gate check, and the ledger format rule; `/s:plan` and
`/s:autopilot` stay untouched.

Evidence:

- Q1 keeps `plugins/s/skills/plan/SKILL.md` out of scope.
- `.shipd/verified/shipd-spec-lint/spec.md` requires only the ledger fields,
  not their values, so the linter needs no change.

### Affected capabilities and files

Three capabilities and about ten files change.

Evidence:

- `context-gate`: new requirement `provisional-entry-check` beside
  `context-sufficiency-checks`; `shipd-spec-format` `plan-document-sections`
  (base 63a3635dc0ef), hash from `spec_status.py base-hash`.
- Files: `plugins/s/skills/build/scripts/spec_gate.py:326-334`,
  `plugins/s/skills/build/tests/test_spec_gate.py`, `.shipd/README.md:186`,
  `AGENTS.md:156`, `README.md:279`, `docs/cheatsheet.md:44,64`,
  `plugins/s/.claude-plugin/plugin.json:4`, the new skill and harness body.
- Runnable premise: `spec_status.py epic-show review-rubric --json` → exit 0,
  lanes keyed `unplanned`/`ready`/`building`/`shipped`, each member with
  `slug`, `state`, `risk`.
- Runnable premise: `spec_status.py locate audience-guides` → exit 0, keyed
  `change:`/`root:`/`dir:`/`status:` block; `--root <that root> status
  audience-guides` → `ready`.
- `plugins/s/skills/build/tests/test_harness_bodies.py:197` forbids
  `subagent`, `sub-agent`, `AskUserQuestion` in ungated bodies.

### No open task-shaping decision

Every task-shaping decision is settled.

Evidence:

- Contract home, gate timing, provisional record: settled by the user, Q1-Q3.
- Sequential planning, dependency order, 4-question dialog batches, and
  agenda read from disk: settled by investigation of
  `plugins/s/skills/autopilot/SKILL.md` and the AskUserQuestion limits.
- Personal memory store: absent, so no preference applied.
