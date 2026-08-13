# Tasks — plan-motivation-first

## 1. Lint rule (test-first)

- [x] 1.1 [req: proposal-header-validation] Extend
      `plugins/s/skills/build/tests/test_spec_lint.py`: a plan with
      `### Non-goals` but no `### Motivation` errors naming the missing
      `### Motivation` subsection; a plan with no `### Details` errors naming
      `### Details`; a plan carrying all three subsections passes. Run the
      suite and observe the new cases fail — the rule does not exist yet.
- [x] 1.2 [req: proposal-header-validation] In
      `plugins/s/skills/build/scripts/spec_lint.py`, extend
      `check_plan_header` to require `### Motivation` and `### Details`
      alongside the existing `### Non-goals` membership check; update the
      docstring and the module-top comment near `REQUIRED_PLAN_SECTIONS`.
      Confirm the 1.1 cases now pass.
- [x] 1.3 [req: proposal-header-validation] Restructure every lint-clean plan
      fixture to the new Idea shape (summary sentence, `### Motivation`,
      `### Details`, `### Non-goals` last):
      `plugins/s/skills/build/tests/fixtures/sample/.shipd/planned/sample-change/plan.md`,
      `plugins/s/skills/onboard/assets/sandbox/.shipd/planned/add-board/plan.md`,
      and the inline plan constructs in `test_spec_gate.py`,
      `test_spec_status.py` (the lint-clean plan near line 408),
      `test_spec_emit.py`, and `evals/tests/test_runner.py`. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      `uvx pytest evals/tests/ -q` until green; leave the never-lint-clean
      minimal plans (e.g. `test_autopilot.py`) untouched.

## 2. Format authority and guidance

- [x] 2.1 [P4] [req: plan-document-sections] In `.shipd/README.md`, rewrite the
      `## Idea` bullet (near line 60) and the linter-enforcement sentence
      (near line 69) to the new order: one-sentence summary, `### Motivation`
      (at most two sentences, grounded — never a guess), `### Details`
      (concrete changes + affected capabilities and impact), `### Non-goals`
      last; note the linter enforces the presence of all three subsections.
- [x] 2.2 [P4] [req: plan-document-sections] In
      `plugins/s/skills/plan/references/emission.md`, rewrite the
      `## plan.md — idea + implementation` element-order list and the
      `dark-mode-toggle` worked example to the new Idea shape, including the
      groundedness rule for `### Motivation`.
- [x] 2.3 [P4] [req: readiness-checklist-gate] In
      `plugins/s/skills/plan/references/readiness.md`, harden item 1: the
      motivation must be stateable in at most two precise sentences grounded
      in the request and repo context; when it cannot be, it is
      un-inferrable and goes to the user before emission.

## 3. Skill behavior and docs

- [x] 3.1 [P4] [req: standalone-invocation] In
      `plugins/s/skills/plan/SKILL.md`, rewrite Ending step 2: the hand-off
      summary leads with the plan's `### Motivation`, then a brief
      Implementation summary; it never lists the artifact files; it keeps
      the change name, worktree location, promoted status, and the
      `/s:build` pointer.
- [x] 3.2 [P4] [req: plan-document-sections] Update the remaining descriptions of
      the Idea layout: `plugins/s/skills/onboard/SKILL.md` (the excerpt
      instruction near line 156 — quote the `### Motivation` alongside
      `### Non-goals`) and the repo `README.md` artifact-layout lines (near
      lines 49 and 58) if they spell out the Idea contents.

## 4. Ship gate

- [x] 4.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      0.6.1 → 0.6.2.
- [x] 4.2 [req: *] Verification barrier: run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      `uvx pytest evals/tests/ -q`; both green.
- [x] 4.3 [req: *] SKILL.md changed — run one local eval case,
      `python3 evals/run.py --case plan-csv-export`, and confirm the session
      emits a lint-clean plan under the new structure.
