# plan-motivation-first

Status: verified

## Idea

Restructure `plan.md`'s Idea section around an explicit `### Motivation`, and
make the plan skill's hand-off summary lead with why-then-how instead of
listing the files it created.

### Motivation

The end-of-plan summary currently inventories artifacts (`plan.md`, delta
specs, `tasks.md`), which tells the user nothing about what is actually being
built, and the plan's motivation lives as unlabeled prose that nothing can
enforce or surface. Making the why an explicit, lint-checked section keeps
every plan grounded in a stated reason — and gives the summary something real
to lead with.

### Details

- `## Idea` gains a fixed subsection order: a one-sentence summary of the
  change, then `### Motivation` (at most two sentences, grounded in the
  planning context — never a guess), then `### Details` (the concrete changes
  plus affected capabilities and impact — today's Idea body), then
  `### Non-goals` last.
- `spec_lint.py` enforces the presence of `### Motivation` and `### Details`
  alongside the existing `### Non-goals` check.
- The plan skill's ending summary leads with the Motivation, then the
  Implementation approach; it no longer enumerates artifact files. The change
  name, worktree, promoted status, and `/s:build` pointer remain.
- Readiness item 1 hardens: a motivation that cannot be stated precisely from
  the provided context is un-inferrable and must be put to the user before
  emission.

Affected capabilities: `shipd-spec-format`, `shipd-spec-lint`, `shipd-plan` (all
modified). Impact: `plugins/s/skills/plan/SKILL.md`,
`references/emission.md`, `references/readiness.md`,
`plugins/s/skills/build/scripts/spec_lint.py` and its tests, `.shipd/README.md`,
the repo `README.md`, the onboard sandbox fixture and its SKILL.md excerpt
text, the sample test fixture, `evals/tests/test_runner.py`, and the plugin
version (0.6.1 → 0.6.2). No new dependencies.

### Non-goals

- No change to `epic.md`'s Introduction grammar — the Motivation/Details
  structure applies to change plans only.
- No rewriting of archived `completed/` plans — they are never re-linted.
- No lint-enforced ordering of the Idea subsections or checking of the
  one-sentence summary and two-sentence Motivation lengths — presence-only
  enforcement, matching the existing `### Non-goals` precedent; order and
  length stay authoring guidance.
- No change to `spec_gate.py` — it locates the `## Idea` line, which is
  untouched.

## Implementation

- **Presence-only lint, three headings.** `check_plan_header` in
  `spec_lint.py` adds `### Motivation` and `### Details` to the same
  membership check that enforces `### Non-goals` today. Rejected:
  guidance-only headings — sessions converge on what the linter enforces, so
  unenforced structure would drift immediately. Rejected: order/length
  checks — prose properties the linter cannot judge reliably; they stay in
  the format docs.
- **Grammar lives in the format authority.** `.shipd/README.md` documents the
  new Idea element order; `emission.md` restates it for authors and reworks
  the `dark-mode-toggle` example to the new shape. The existing content of
  the Idea body (concrete changes, capabilities, impact) moves under
  `### Details` — nothing is dropped.
- **Motivation groundedness is a readiness concern, not a lint concern.**
  `readiness.md` item 1 gains the rule: the motivation must be stateable in
  at most two precise sentences grounded in the request and repo context;
  otherwise it is un-inferrable and goes to the user (fast-path question
  round or depth-path grill) before emission. The linter cannot detect a
  guessed motivation; the readiness gate is where judgment already lives.
- **Hand-off summary reads the plan, not the tree.** SKILL.md's Ending step
  2 is rewritten: summarize what is being built by leading with the plan's
  `### Motivation`, then the `## Implementation` approach in brief. No
  artifact-file inventory. The pointer to `/s:build`, the change name, and
  the worktree stay — they are actionable, not inventory.
- **Fixture fallout is contained.** Only plans that must lint clean change:
  the sample test fixture, the onboard sandbox `add-board` plan, and the
  lint-clean plan constructs in `test_spec_lint.py`, `test_spec_gate.py`,
  `test_spec_status.py`, `test_spec_emit.py`, and `evals/tests/test_runner.py`.
  Minimal plans in tests that never pass full lint (e.g. `test_autopilot.py`)
  stay untouched.

Risk: this change's own `plan.md` is linted mid-build once the new rule
lands — guarded by authoring it in the new structure from the start (this
document already carries Motivation/Details/Non-goals in order).
