# plan-deep
Status: verified
Planned-at: 337a5b0d692ae787a5d1bbdda3c752239e6d2788
Gated-hash: 5fbb74b9af48

## Idea

Add a `/s:plan-deep` skill that walks one spec's riskiest pieces with the user, scored by a rubric `/s:epic-grill` shares and reports.

### Motivation

`/s:epic-grill` gates every member at one depth and shows no risk view, so a user cannot see which specs deserve a closer look before `/s:autopilot` builds them. Nothing then walks them through a risky spec piece by piece to adjust it, either after a grill or on a single change.

### Details

- A shared rubric, `plugins/s/skills/plan-deep/references/rubric.md`, scores a spec low/medium/high and flags which of its pieces matter most. Both skills load it from that one path.
- `/s:epic-grill` prints a risk table for the selected members after the last gate. When any member scores medium or higher, it prints `/s:plan-deep <epic> <member> ...` beside the table and again as the very last line of its output.
- A new `/s:plan-deep` skill takes one change, or an epic with optional members. It restates the spec, walks each flagged piece one step at a time, edits the spec in place, and re-gates it. It can call `/s:research` for an external unknown.

Affected capabilities: `shipd-plan-deep` (added), `shipd-epic-grill` (one added requirement). Impact: new skill, rubric, and harness body; the grill's skill and body; two contract tests; `README.md`, `docs/cheatsheet.md`, `AGENTS.md`; the plugin version.

### Non-goals

- No risk score saved into `plan.md`, and no linter, emit, or gate change.
- No new `/s:deep-research` skill; the existing `/s:research` is the research hook.
- No spike or code from `/s:plan-deep`; it plans only and never builds.
- The grill never runs `/s:plan-deep` inline; it prints the command and stops.

## Implementation

- **Rubric home.** `plan-deep/references/rubric.md` owns the rubric, the way `document/references/question-brief.md` serves several skills. The grill and both harness bodies cite that path; nothing restates the scale. Rejected: a copy per skill, which drifts.
- **Rubric shape.** Five axes, each low/medium/high: the epic table's Code, Integration, Unknowns, and Risk, re-judged against the plan as written, plus Novelty on Liz Keogh's 1–5 scale (1–2 low, 3 medium, 4–5 high). Shape Up rabbit-hole checks and seven coverage categories (scope and behavior, interfaces and data shapes, integration and dependencies, edge cases and failure, constraints and trade-offs, completion signals, terminology) refine it. The overall level is the highest axis. Any rabbit hole lifts it to at least medium. Novelty 4–5, or a Missing interface category, makes it high. Source: research `epic-complexity-map`.
- **Piece flagging.** A piece is one decision, one delta requirement, or one task group. The rubric flags a piece that touches a medium/high axis, a rabbit hole, a Partial or Missing category, a ledger entry carrying `**Relied on by:**`, or a cross-member interface. Flagged pieces run high first, then by `**Relied on by:**` count, then document order. One closing step summarizes every unflagged piece.
- **Score lives on screen (Q2).** The grill prints `| Member | Code | Integration | Unknowns | Risk | Novelty | Overall | Why |` and passes medium/high slugs on the command line. `/s:plan-deep <epic>` with no members re-scores with the same rubric.
- **Grill hand-off (Q4).** The risk table sits after the per-member summaries and before the preflight. With any medium/high member, the command prints under the table and again after the `/s:autopilot` line or the fail list, as `There are complex specs worth a deep plan, kick it off with:`, a blank line, then the command alone on its line. Rejected: asking to run inline, which breaks the grill's print-and-stop ending.
- **Walkthrough (Q3).** Each step restates one flagged piece, says why the rubric flagged it, and ends on a plain-text numbered round: keep, change, research, or cut/mark out of bounds. A typed round is used because the step carries prose. Novelty 5 always offers cut or out of bounds, since the skill cannot spike.
- **Edits and records.** Plan-deep edits only the focused member's installed `plan.md`, delta specs, and `tasks.md`. Each changed decision appends a `## Questions and answers` entry with `**Answered by:** USER`, continuing the numbering. It never edits a sibling member or the epic. It names a sibling whose `**Relied on by:**` link or shared interface the edit touches, and flags an epic-wide change for `/s:epic <epic> amend`.
- **Status path.** It accepts a change at `draft`, `ready`, or `rejected` and refuses `active`, `complete`, or `verified`. After its edits it runs `spec_gate.py <change> --root <root>`. A pass leaves or makes it `ready`; exit 2 works the findings, asks what remains, and re-gates. It never runs `set-status`.
- **Research (Q1).** When a piece rests on an external unknown, it offers `/s:research <question>`, invoked by reference only while the user is present, then reads the report back with `cat research <slug>` and cites it in `plan.md` prose.
- **Endings.** Standalone ends with `/s:build` alone on its line. Epic mode walks members in the order given, runs `autopilot.py <epic> --preflight` once, relays its `warn`/`fail` lines, and prints `/s:autopilot <epic>` only on exit 0.

Risk: a judgement rubric scores unevenly across runs. The grill passes explicit slugs so one scoring drives the follow-up, and the score only steers a walkthrough the user controls.

## Questions and answers

### Q1: Which skill is the research hook?
- **Question:** Should `/s:plan-deep` call the existing `/s:research` or a new `/s:deep-research`? Options: (1) `/s:research`; (2) new skill. Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option 1. "Deep research" was the build name of the `autonomous-delivery` member that shipped as `/s:research`; it is human-driven, so plan-deep calls it only with the user present.
- **Cited:** epic/autonomous-delivery

### Q2: Where does the risk score live?
- **Question:** Print the grill's risk table only and pass medium/high slugs on, or save a risk section into each `plan.md`? Options: (1) print only; (2) save. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Print only; the grill passes medium/high member slugs into the plan-deep command.
- **Queued:** q-epic-grill-risk-score-persistence

### Q3: What is one walkthrough step?
- **Question:** One step per rubric-flagged piece, highest risk first with a closing summary of the rest, or every piece in document order? Options: (1) flagged pieces; (2) everything. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** One step per flagged piece, highest risk first, unflagged pieces summarized in one closing step.
- **Queued:** q-plan-deep-walkthrough-step-unit

### Q4: How does the grill offer plan-deep?
- **Question:** Print a `/s:plan-deep <epic> <member> ...` command and stop, or ask to run it inline? Options: (1) print; (2) inline. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Print the command beside the risk table, and also close the whole output with "There are complex specs worth a deep plan, kick it off with:" and the command on its own line, whenever a member scores medium or higher.
- **Queued:** q-epic-grill-plan-deep-offer

## Readiness attestation

### Problem and motivation

The grill gates every member at one depth with no risk view, and no skill walks a risky spec piece by piece.

Evidence:

- `plugins/s/skills/epic-grill/SKILL.md:239-274` ends with summaries, preflight, and `/s:autopilot`; no risk output.
- Requirement `epic-grill-amend-gate` in `shipd-epic-grill` defines that ending.

### Scope and non-goals

A new skill, a shared rubric, and an added grill requirement; no engine, lint, or plan-format change.

Evidence:

- In scope: `plugins/s/skills/epic-grill/SKILL.md`, `plugins/s/harness/bodies/epic-grill.md`, new `plugins/s/skills/plan-deep/`.
- Out of scope: `plugins/s/skills/build/scripts/` is not edited.

### Affected capabilities and files

Two capabilities and about ten files, because the skill is new and the grill gains one ending step.

Evidence:

- Capability `shipd-epic-grill`: one ADDED requirement; `epic-grill-amend-gate` (base e77da4cbf776) is left unchanged.
- Capability `shipd-plan-deep`: new.
- Files: `plugins/s/skills/epic-grill/SKILL.md:239`, `plugins/s/harness/bodies/epic-grill.md:80-88`, `plugins/s/skills/build/tests/test_epic_grill_contract.py`, `README.md:283`, `docs/cheatsheet.md:44,61`, `AGENTS.md:157`, `plugins/s/.claude-plugin/plugin.json`.
- `plugins/s/skills/build/tests/test_harness_bodies.py:238` requires one body per `SKILL.md` directory; `:463` caps a rendered body under 150 lines.
- Runnable premise: `spec_status.py base-hash shipd-epic-grill epic-grill-amend-gate` → `e77da4cbf776`.
- `plugins/s/skills/build/scripts/spec_gate.py:12` documents that a passing `ready` plan stays `ready` and a failing one becomes `rejected`.

### No open task-shaping decision

Every task-shaping decision is settled.

Evidence:

- Research hook (`/s:research`): oracle, Q1.
- Score persistence (print only): user, Q2.
- Walkthrough unit (flagged pieces): user, Q3.
- Grill hand-off (print, plus a closing line): user, Q4.
- Rubric home and re-gate path: investigation.
