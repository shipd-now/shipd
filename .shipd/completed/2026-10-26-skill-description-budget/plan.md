# skill-description-budget
Status: verified
Epic: context-budget
Planned-at: 77880ceb04902914a42c88ccabe37f372b59eaa9
Gated-hash: 63a2d9951e25

## Idea

Trim every skill's `description` to its harness body one-liner plus its
unchanged trigger phrases, at most 300 characters each, and hold that budget
with a test.

### Motivation

Every Claude Code session with shipd installed loads the skill listing, and
the 31 shipd descriptions total about 19,000 characters. Claude Code fits that
listing into 1% of the context window and drops descriptions to make room, so
11 `s:*` skills already appear with no description at all.

### Details

- Rewrite the frontmatter `description` of all 31
  `plugins/s/skills/*/SKILL.md` files: body one-liner, then the existing
  `Trigger phrases:` clause verbatim. Folded total drops from 18,955 to about
  6,300 characters.
- New `plugins/s/skills/build/tests/test_skill_descriptions.py` enforcing the
  budget and the shape.
- One `AGENTS.md` bullet naming the rule.
- A `/context` reading before and after; ship only on a real gain.
- Bump the plugin version.

Affected capabilities: `skill-listing` (new). Impact: 31 SKILL.md
frontmatters, one new test, `AGENTS.md`, and
`plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No change to any SKILL.md body or to what any skill does.
- No change to the harness body one-liners, the generated command files, or
  agent descriptions.
- No `when_to_use` field, `skillOverrides`, or listing-budget setting.
- No harness other than Claude Code.

## Implementation

- **Budget** (Q1): 300 characters per folded `description`. Every skill fits
  its one-liner plus its full trigger clause (longest: `workspace`, 298).
  The number lives once, as `DESCRIPTION_BUDGET` in the new test. Rejected:
  250, which would force rewording one-liners; 400, which leaves a third of
  today's text in place.
- **Text source** (Q2): the description is
  `harness_bodies.description(<name>)`, a space, then
  `Trigger phrases: "a", "b", "/s:<name>".` The one-liners are already
  curated, short, and match what other harnesses show. The test enforces
  that exact shape, so the two surfaces cannot drift. Rejected: hand-written
  text per skill, which creates a second summary to keep in sync.
- **Trigger phrases** (Q3): copied verbatim, never reworded or dropped. The
  build compares each skill's phrase set before and after the edit, once.
  The permanent test requires a non-empty clause holding `/s:<name>`, and
  the existing `TriggerPhraseTest` keeps `"record a demo"` on `demo` only.
  Rejected: a checked-in phrase snapshot, a second file to edit on every
  trigger change.
- **Reading the description.** Take the frontmatter between the first two
  `---` lines, find `description: >-`, join the indented lines that follow
  with single spaces, and strip. This matches YAML folding. Keep the `>-` block style: the colon in
  `Trigger phrases:` would break a plain scalar.
- **Test** (`plugins/s/skills/build/tests/test_skill_descriptions.py`,
  stdlib, imports `harness_bodies` from the sibling scripts directory (`plugins/s/skills/build/scripts`) like
  `test_harness_bodies.py`): loops over every skill dir holding a
  `SKILL.md`. One test asserts length ≤ `DESCRIPTION_BUDGET` and names each
  failing skill with its length. One asserts the shape with the regex
  `^(?P<lead>.+) Trigger phrases: (?P<p>"[^"]+"(, "[^"]+")*)\.$`, `lead`
  equal to the body one-liner and `"/s:<name>"` among the phrases. A
  fixture-text test proves a 301-character description is reported.
- **Live proof** (Q4): read Claude Code's `/context` before any SKILL.md
  edit and after the edits, each from an empty scratch directory, with
  `claude -p "/context" --output-format json --max-turns 1 --plugin-dir
  <worktree>/plugins/s --settings '{"enabledPlugins":{"s@shipd":false}}'`.
  Both readings load only the worktree's plugin copy, with the installed
  one disabled, so they compare like with like. Each reading must list the
  `s:*` skills exactly once with Source "Plugin (s)"; if they appear twice
  or not at all, the build stops and reports. The `result` field is a markdown report with a
  Skills category total and a per-skill table (Skill | Source | Tokens); a
  skill whose description was dropped shows as `< 20` tokens. The member
  ships when the after reading lists no `s:*` skill at `< 20` tokens, or
  when the Skills category total drops. Without either, the build stops
  and reports both readings, and the member is dropped, per the epic.
- **No checked-in ceiling** (Q5): the `/context` reading is the only
  measurement; the change adds or lowers no budget file.
- **PR evidence.** Both `/context` readings: the Skills category total
  before and after, the `s:*` rows at `< 20` tokens in each, the gain
  verdict, and the folded description character totals.
- **Version.** Patch bump in `plugins/s/.claude-plugin/plugin.json` to one
  above main's value at build time (AGENTS.md rule).

Risk: a shorter description could make Claude pick a skill less often. Every
trigger phrase stays, and the dropped "Use when asked to" prose mostly
repeated those phrases. A second risk: the listing is already capped at the
budget, so the Skills total may drop less than the character cut.
Any real gain still ships, and the cut is what stops descriptions being
dropped.

## Questions and answers

### Q1: What per-skill budget holds each skill description?
- **Question:** Options: (1) 300 folded characters, fitting each body
  one-liner plus its full trigger clause; (2) 250, forcing some one-liners to
  be reworded; (3) 400. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1: every skill fits without rewording, and the 31
  descriptions drop from 18,955 to about 6,300 characters.
- **Queued:** q-skill-description-budget-per-skill-limit

### Q2: Where does each shortened description come from?
- **Question:** Options: (1) the harness body one-liner plus the existing
  `Trigger phrases:` clause, with a test enforcing that shape; (2)
  hand-written text per skill, the test checking only length and a trigger
  clause. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1: one curated summary per skill serves both surfaces,
  and the test stops them drifting.
- **Queued:** q-skill-description-budget-description-source

### Q3: How is keeping every trigger phrase guarded?
- **Question:** Options: (1) a one-off build-time comparison with main's
  phrases, plus a permanent test for a non-empty clause holding `/s:<name>`;
  (2) a checked-in snapshot of every skill's phrases compared by a test.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1: trimming copies phrases verbatim, so a one-off check
  proves it, and trigger changes later need no snapshot edit.
- **Queued:** q-skill-description-budget-trigger-guard

### Q4: How does this member prove its gain?
- **Question:** What reading proves the trim helped, and when does the
  member ship?
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** A before and after reading of Claude Code's `/context` from
  `claude -p "/context" --output-format json --max-turns 1 --plugin-dir
  <worktree>/plugins/s --settings '{"enabledPlugins":{"s@shipd":false}}'`,
  run from an empty scratch directory: the before reading before any
  SKILL.md edit, the after reading once the edits are done, both on the
  worktree's plugin copy with the installed one disabled. Each reading
  must list the `s:*` skills exactly once with Source "Plugin (s)", or the
  build stops and reports. The member ships when no `s:*` skill is listed
  at `< 20` tokens after the edit, or when the Skills category total
  drops. The PR body carries both readings.

### Q5: Does this member hold its gain with a checked-in ceiling?
- **Question:** Does the change add or lower a checked-in context budget
  file, or is the before and after reading enough?
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** No ceiling: the before and after `/context` reading is the
  only measurement, and the change edits no budget file.

## Readiness attestation

### Problem and motivation

Skill descriptions are the largest shipd contributor to every session's
context, and they overflow Claude Code's listing budget.

Evidence:

- epic/context-budget Introduction: 31 descriptions about 20 KB; 11 `s:*`
  skills show no description.
- epic/context-budget Design: "`skill-description-budget` shortens
  descriptions to a per-skill budget while keeping each trigger phrase,
  enforced by a test."
- code.claude.com/docs/en/skills, "Skill descriptions are cut short": the
  listing budget is 1% of the context window; overflow drops descriptions
  of the least-invoked skills.

### Scope and non-goals

31 frontmatter blocks, one test, one doc bullet, and the version bump.

Evidence:

- Epic non-goal: "descriptions may shrink, behaviour may not."
- Epic Decisions: "Every optimisation proves itself"; the proof is a
  before and after `/context` reading (Q4).

### Affected capabilities and files

One new capability and the files named in Details.

Evidence:

- Capability `skill-listing` (new); no verified capability owns SKILL.md
  description length. `project-readme` asks README entries to stay
  consistent with the frontmatter; shorter text stays consistent.
- `harness_bodies.description(command)` returns the one-liner;
  `test_harness_bodies.py:240-246` asserts bodies and skills share one id
  set, so every skill has a one-liner.
- `.github/workflows/ci.yml:51` runs `plugins/s/skills/build/tests`.
- Runnable premise: a folding script over the 31 SKILL.md files gives
  18,955 characters; every description ends in a `Trigger phrases:` clause.
- Runnable premise: one-liner + space + trigger clause per skill totals
  6,289 characters, maximum 298 (`workspace`).
- `test_epic_grill_contract.py:90` needs "on a green preflight" in the
  frontmatter; the epic-grill one-liner holds it.

### No open task-shaping decision

Every task-shaping decision is settled.

Evidence:

- Budget, text source, trigger guard: planner defaults Q1, Q2, Q3.
- Gain rule and no checked-in ceiling: user, Q4, Q5.
