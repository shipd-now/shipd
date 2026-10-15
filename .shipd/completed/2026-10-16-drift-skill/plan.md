# drift-skill
Status: verified
Epic: autopilot-preflight
Theme: reliability

## Idea

Add `/s:drift`, a thin read-only skill over `spec_status.py drift` that puts
only the flagged members' plans and finding-scoped diffs before the session's
model and returns one verdict per member: `holds`, `revise`, or `conflict`.

### Motivation

The unattended run (`/s:autopilot` and the detached driver) can measure drift
with the verb but has no judge for it, so a member whose cited files moved
either stops to ask a human or builds on a plan that no longer matches `main`.

### Details

- `/s:drift <change> | --epic <slug> [--base <ref>] [--json]` mirrors the
  verb's flags; the skill passes `--base` and `--epic` through unchanged.
- Verb exit 0 → every member clean or skipped, no model runs; 4 → judge each
  member with findings; 1 or 2 → relay the engine's error and stop.
- Evidence per flagged member is bounded to `cat change`, the diffs behind
  each finding, the current master for a `stale-base`, and the epic's Decisions.
- A fixed `## Drift verdicts` block ends the report; `--json` makes the whole
  response one object.

Affected capabilities: `shipd-drift` (added). Impact:
`plugins/s/skills/drift/SKILL.md`, `plugins/s/harness/bodies/drift.md`,
`plugins/s/skills/build/tests/test_drift_skill_contract.py`, `README.md`,
`docs/cheatsheet.md`, `AGENTS.md`, `plugins/s/.claude-plugin/plugin.json`.
No engine code, no new dependency.

### Non-goals

- No re-plan, re-gate, parking, or `git fetch` — `autopilot-unattended-run`
  and `detached-drift-replan` own the loop around the verdict.
- No change to the verb's shapes or exit codes; no `Gated-hash` check.
- No spawned agent and no question dialog: the skill runs unattended.
- No `docs/` page beyond the cheatsheet row.

## Implementation

- **Judgment runs in the invoking session** (Q1): the skill reads the evidence
  below and judges in place; the harness body stays ungated, so a bare harness
  runs it verbatim. Rejected: one spawned judge per member — a gated body plus
  fallback reference for no bound the evidence rule does not already give.
- **Invocation → verb.** Strip the skill's own `--json`; run
  `python3 "$S/spec_status.py" drift <args>` once in text form (relayed
  verbatim as the report's first section, as `/s:status` relays) and once with
  `--json` for the member list. Under `--json`, run only the JSON form. The
  verb's `root` field names each member's hosting root for every later read.
- **Exit branches.** `0`: print `clean:`/`skipped:` lines, no plan or diff is
  read. `4`: judge every member whose `findings` is non-empty. `1`/`2`: relay
  the `Error:`/usage text and stop — under `--json`, emit the object with
  `error` set and empty arrays (the `/s:review` cannot-run rule).
- **Evidence set, per flagged member** — nothing else is read:
  `spec_status.py --root <root> cat change <member>`;
  `spec_status.py cat epic <slug>` once per run (the plan's `Epic:` header);
  per `file-drift`: `git -C <root> diff <planned_at>..<base.sha> -- <path>`,
  and when that exceeds 400 lines, `git log --format='%h %s'` for the path
  plus the hunks naming an identifier the plan cites; per `symbol-gone`:
  `git -C <root> grep -l -w -F <symbol> <planned_at>` (strip the `<sha>:`
  prefix) → the diff over those paths, plus `git log --format='%h %s'
  -S<symbol> <planned_at>..<base.sha>`; per `stale-base`:
  `spec_status.py --root <root> cat verified <capability>` against the
  delta's MODIFIED entry.
- **Verdict rules.** `holds`: no assumption the plan's Implementation, tasks,
  or delta scenarios make about the drifted paths, symbols, or master changed
  (shifted line citations, unrelated edits). `revise`: an assumption broke —
  a called symbol or signature gone, a structure the tasks edit moved, a
  modified master requirement rewritten — and a revision inside the plan's
  `**Answered by:** USER` entries and the epic's Decisions repairs it.
  `conflict`: the repair, or the drift itself, contradicts a `USER` entry or
  an epic Decision; the reason names `Q<n>` or the Decision's bold name.
  `PLANNER` and `ORACLE` entries never raise `conflict`. When the evidence
  cannot show an assumption holds, the verdict is `revise`, never `holds`.
- **Text block** (Q2), last in the report, one line per member in the verb's
  order: `<member>: holds — <reason>`; `<member>: revise — <reason>; revise:
  <sections or tasks>`; `<member>: conflict — <reason>; contradicts: Q<n> |
  Decision "<name>"`; then `clean: a, b`, `skipped: c (<reason>)`, and
  `verdicts: <n> holds, <n> revise, <n> conflict; <n> clean, <n> skipped`.
  Single-change mode prints the same block over one member.
- **JSON shape** (Q2): `{"mode":"epic"|"change","epic","change","base":
  {"ref","sha"},"verdicts":[{"member","root","planned_at","verdict","reason",
  "contradicts":null|"Q<n>"|"Decision: <name>","revise":null|"<what>",
  "findings":[verb finding objects verbatim]}],"clean":[...],"skipped":
  [{"member","reason"}],"error":null|"<line>"}` — valid JSON, no fence, no
  prose, mirroring `review/references/json-output.md`. Rejected: a verdict
  file in the change dir — a read surface writing into the spec tree.
- **Ending.** Name the next step per verdict — `revise`: revise the plan and
  re-gate with `spec_gate.py <change>`; `conflict`: a human decision on the
  named `Q<n>`/Decision — and stop; the skill performs neither.
- **Registration.** `SKILL.md` frontmatter `name: drift`, trigger phrases
  `"drift"`, `"check drift"`, `"has the plan drifted"`, `"/s:drift"` (no other
  skill claims them); body `harness/bodies/drift.md` opening with the
  description marker, no gate, none of `subagent`, `sub-agent`,
  `AskUserQuestion`; rows in `README.md` (Orchestration table, after
  `/s:autopilot`), `docs/cheatsheet.md` (Unattended group; table row between
  `/s:document` and `/s:drive`, linted with `docs_lint.py`), and `AGENTS.md`'s
  skill roll after `/s:epic-grill`.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` to the next patch
  above `main` at build time (`0.6.292` when planned).

Risk: a diff-bounded judge misses drift in uncited files — accepted, the
epic's rule; the `revise`-on-doubt tie-break keeps the error on the cheap side.

## Questions and answers

### Q1: Where does the judgment of a flagged member run?
- **Question:** Options: (1) in the invoking session, reading only the
  member's plan and the finding-scoped diffs, with an ungated harness body;
  (2) one spawned agent per flagged member, the skill collating, with a
  gated body and fallback reference. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** USER accepted the default: judgment runs in the invoking session
  over the bounded evidence set, with an ungated harness body; no spawned
  agent.
- **Queued:** q-drift-skill-judgment-locus

### Q2: What is the verdict output contract?
- **Question:** Options: (1) a report ending in a fixed `## Drift verdicts`
  block plus `--json` making the response one object, no file written; (2)
  text only; (3) also write a verdict file into the change directory.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** USER accepted the default: a fixed `## Drift verdicts` block
  ends the report, `--json` makes the whole response one object, and no file
  is written.
- **Queued:** q-drift-skill-output-contract
- **Relied on by:** autopilot-unattended-run, detached-drift-replan

## Readiness attestation

### Problem and motivation

The run can measure drift but cannot judge it, so it asks or builds blind.

Evidence:

- Epic `autopilot-preflight`: Design "Detection layer" (`/s:drift` gives the
  model only flagged diffs; one verdict per member), Decision "Mid-run drift
  is re-planned, not asked".
- `drift-verb` plan `### Non-goals`: "No model, `/s:drift` skill".

### Scope and non-goals

One skill, its body, three registry rows, a contract test, and the bump; the
loop around the verdict belongs to later members.

Evidence:

- Epic `## Changes` rows `autopilot-unattended-run` and
  `detached-drift-replan` (After: `drift-skill`).
- `plugins/s/skills/explain/SKILL.md:16-27` — the read-only contract copied.

### Affected capabilities and files

One new capability and seven files, because a command needs a skill, a body,
its registry rows, and a test, and every `plugins/s/` change bumps the version.

Evidence:

- Capability `shipd-drift` (added); model `shipd-explain`.
- `plugins/s/skills/build/tests/test_harness_bodies.py:235-247` body/skill
  parity, `:197` forbidden ungated tokens, `:306-316` trigger uniqueness;
  `README.md:276`; `docs/cheatsheet.md:44,60-61`; `AGENTS.md:156-157`;
  `plugins/s/skills/build/tests/test_epic_grill_contract.py:1-30` (test
  pattern); `plugins/s/skills/build/scripts/session_driver.py:78-108`
  (`claude -p --output-format json`); `autopilot.py:449-490`.
- Runnable: `harness_bodies.commands()` → 27 ids, `explain` present,
  `description('explain')` non-empty.
- Runnable: `spec_status.py cat change drift-verb` from the root → prints the
  worktree-hosted plan, exit 0; `cat epic autopilot-preflight` → exit 0.
- Runnable: `git diff 35db51c..main -- plugins/s/.claude-plugin/plugin.json`
  → unified diff, exit 0; `git log --format='%h %s' -Scmd_check_base
  35db51c..main -- <path>` → exit 0; `git grep -l -w cmd_check_base 35db51c
  -- plugins/s/skills/build/scripts` → `35db51c:<path>`, exit 0.
- Runnable: `spec_merge.py:79-80` applies a `stale-base` with a take-newer
  warning, so that finding is judged, not mechanically fatal.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Judgment locus: PLANNER default, Q1, oracle `INSUFFICIENT`.
- Output contract: PLANNER default, Q2, oracle `INSUFFICIENT`.
- Flags, exit codes, `skipped` relay: drift-verb's plan (its Q3).
- Verdict semantics and clean-member rule: epic Decisions, investigation.
