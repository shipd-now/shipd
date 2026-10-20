# plan-mode-guard
Status: verified
Planned-at: aa3b0a8f7d00cbe7be74eabdf743a958aa11afda
Gated-hash: 89dcfbc4ca73

## Idea

Teach every writing shipd skill to stop cleanly under Claude Code plan mode
instead of mixing its flow with plan mode's outputs.

### Motivation

A user who invoked `/s:plan` under plan mode got a hybrid run: shipd's
investigation, then plan mode's plan file and `ExitPlanMode`, with no
worktree, oracle, emission, or gate. The plan-mode block claims to override
every other instruction, and no shipd skill names the conflict.

### Details

- Add the shared reference `plugins/s/skills/document/references/harness-plan-mode.md`.
- Insert one `## Harness plan mode` section into 25 writing skills' SKILL.md.
- Add a harness plan mode bullet to `/s:plan`'s "What still stops the flow" list.
- Add `plugins/s/skills/build/tests/test_plan_mode_guard_contract.py`.

Affected capabilities: `shipd-interaction` (one added requirement).

### Non-goals

- No change to harness bodies under `plugins/s/harness/bodies/`; only
  Claude Code has this plan-mode block.
- No clause in the read-only skills `duck`, `drift`, `explain`, `memory`, or
  `review`; they run unchanged under plan mode.
- No detection code; the rule is instruction text only.

## Implementation

- **Semantics: investigate, then stop (user choice, Q1).** Under plan mode a
  writing skill runs its read-only steps, prints what it found, and stops
  before its first write. Rejected: proceeding anyway, because plan mode
  refuses edit tools and the flow would break mid-run. Rejected: stopping
  before any work, which gives the user nothing for the turn.
- **Roster: every skill except the read-only five (user choice, Q2).** The
  test computes the roster as every `plugins/s/skills/*/SKILL.md` minus
  `duck`, `drift`, `explain`, `memory`, `review`, so a new skill fails until
  it carries the clause. Today that is 25 skills.
- **Shape: inline name plus shared reference**, mirroring the question-brief
  pattern. The rule's sentence stays inline in each SKILL.md, so a skipped
  reference read never drops it. The reference is staged verbatim at
  `artefacts/harness-plan-mode.md`; copy it byte for byte.
- **Inline section, exact text.** Insert this block, followed by one blank
  line, directly above the first level-2 heading outside a code fence in
  each roster SKILL.md:

  ```markdown
  ## Harness plan mode

  **Harness plan mode never replaces this skill's output.** When the session
  is in Claude Code plan mode, run only this skill's read-only steps. Stop
  before the first write and ask the user to exit plan mode and re-invoke.
  Never write the harness plan file, call `ExitPlanMode`, or mix in plan
  mode's outputs. Details:
  `${CLAUDE_PLUGIN_ROOT}/skills/document/references/harness-plan-mode.md`.
  ```

- **Plan's stop list, exact text.** In `plugins/s/skills/plan/SKILL.md`,
  insert this bullet directly above the line "Anything not on this list
  proceeds without asking.", after the "A foreign-project brief" bullet and
  its blank line:

  ```markdown
  - **Harness plan mode** — the session is in Claude Code plan mode ("Harness
    plan mode" above). Skip the worktree, investigate read-only, and print the
    findings digest. Then stop before the oracle rung, any question round, and
    emission, and ask the user to exit plan mode and re-run `/s:plan`.
  ```

  Keep one blank line between this bullet and the "Anything not on this
  list" line.
- **Test, mirroring `test_question_brief_contract.py`.** Constants
  `CLAUSE = "Harness plan mode never replaces this skill's output."`,
  `POINTER = "skills/document/references/harness-plan-mode.md"`, and
  `READ_ONLY = {"duck", "drift", "explain", "memory", "review"}`. Tests: the
  reference exists and its first line is `<!-- doc-type: reference -->`; the
  reference contains the headings `The rule`, `Read-only steps`, `Writes`,
  `What never happens`, `The stop message`; the roster holds at least 25
  skills; every roster SKILL.md contains `CLAUSE` and `POINTER`; no
  read-only SKILL.md contains `CLAUSE`; the plan SKILL.md contains
  `- **Harness plan mode** —`.

Risk: the new section could change a phrase another test pins. The guard is
running the full build suite after the edits.

## Questions and answers

### Q1: What does a writing skill do under plan mode?
- **Question:** When a writing shipd skill is invoked under Claude Code plan
  mode, should it (a) stop before any work, (b) proceed and treat the
  invocation as authorization, or (c) investigate read-only, then stop
  before the first write? Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option (c): run the read-only steps, then stop before the first
  write and ask the user to exit plan mode and re-invoke.
- **Queued:** q-writing-skill-under-harness-plan-mode

### Q2: Which skills carry the rule?
- **Question:** Should the plan-mode rule live in (a) every SKILL.md except
  the five read-only skills, with a computed-roster test, (b) only plan,
  build, and fix, or (c) every SKILL.md? Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option (a): every SKILL.md except `duck`, `drift`, `explain`,
  `memory`, and `review`, enforced by a computed-roster test.
- **Queued:** q-plan-mode-rule-skill-roster

## Readiness attestation

### Problem and motivation

Under plan mode a shipd writing skill gives way to plan mode's outputs and
runs half of each flow, because no skill names the conflict.

Evidence:
- The user supplied the other session's account: plan file written,
  `ExitPlanMode` called, no worktree, oracle, `spec_emit.py`, or
  `spec_gate.py`.
- `grep -rn -i "plan mode\|ExitPlanMode\|EnterPlanMode" plugins/s .shipd/verified`
  returned no hits.

### Scope and non-goals

One added requirement, one reference, a 25-skill inline section, one stop-list
bullet, and one test; harness bodies and read-only skills stay out.

Evidence:
- `### Non-goals` above names the three exclusions.

### Affected capabilities and files

`shipd-interaction` gains one requirement; the edits land in 25 SKILL.md
files, one new reference, and one new test.

Evidence:
- `ls plugins/s/skills | grep -vxE 'duck|drift|explain|memory|review' | wc -l`
  printed `25`.
- `shipd-interaction` already owns the cross-skill rules
  `question-rejection-recovery`, `dialog-prose-separation`, and
  `question-brief`.
- Each roster SKILL.md has a level-2 heading outside a code fence (an awk
  scan printed one per skill), so the insertion point exists everywhere.
- `python3 -B -m unittest plugins/s/skills/build/tests/test_question_brief_contract.py`
  ran 5 tests, `OK`; the new test follows its layout.
- `python3 -B plugins/s/skills/document/scripts/docs_lint.py plugins/s/skills/document/references/question-brief.md`
  exited 0, so the same lint applies to the new reference.
- Only `semantic-review` and `shipd-explain` own SKILL.md line ceilings, and
  neither skill is in the roster.

### No open task-shaping decision

Semantics and roster are the user's typed answers; placement and wording are
fixed above.

Evidence:
- Q1 and Q2 in the ledger above.
