# Tasks — oracle-qa-ledger

## 1. Engine — completed-change reads

- [x] 1.1 [P1] [req: mediated-read-verb] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add tests: `cat
      change <slug>` on a change present only under `completed/<date>-<slug>/`
      prints its artifacts with `--- <relpath>` separators and exits 0; with
      two archives `completed/2026-01-01-<slug>/` and
      `completed/2026-02-02-<slug>/` the newer one prints; a slug in neither
      `planned/` nor `completed/` still exits non-zero. Run the file and
      observe the new tests fail.
- [x] 1.2 [P2] [req: mediated-read-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`, extend `cmd_cat`'s
      `change` branch to fall back from `planned/<slug>/` to the
      lexicographically last `completed/*-<slug>/` directory (reuse the glob
      pattern already used by the status resolver around line 704). Confirm
      the 1.1 tests pass.

## 2. Engine — ledger lint

- [x] 2.1 [P1] [req: qa-section-validation] In
      `plugins/s/skills/build/tests/test_spec_lint.py`, add tests for the
      `## Questions and answers` plan section: absent section produces no
      finding; an empty present section errors; a first entry headed
      `### Q2:` (non-sequential) errors naming the entry; an entry missing
      `**Question:**`, `**Answered by:**`, or `**Answer:**` errors naming
      the entry; a conforming two-entry section produces no finding. Run and
      observe them fail.
- [x] 2.2 [P2] [req: qa-section-validation] In
      `plugins/s/skills/build/scripts/spec_lint.py`, add a
      `check_plan_qa_section` pass (modeled on the epic `## Research`
      validation and `_section_lines`) wired into the change lint, erroring
      per the 2.1 cases. Confirm the 2.1 tests pass.

## 3. Format authority

- [x] 3.1 [P3] [req: plan-document-sections] In `.shipd/README.md`, document the
      optional `## Questions and answers` plan section: entry grammar
      (`### Q<n>: <summary>` sequential from `Q1`; `**Question:**`,
      `**Verdict:**`, `**Answered by:**` (`ORACLE`|`USER`, directly above
      the answer), `**Answer:**` fields; `**Cited:**` on `ANSWER`,
      `**Queued:**` on `INSUFFICIENT`), next to the existing plan-section
      grammar.

## 4. Plan skill

- [x] 4.1 [P3] [req: plan-qa-ledger, oracle-resolution-visibility] In
      `plugins/s/skills/plan/SKILL.md`, extend "The ask-mikk rung"'s
      "Keep oracle-settled decisions visible" bullet: assign each
      consultation a sequential `Q<n>` reference, report it as
      `Q<n> — <question summary> → <answer summary>` with settler and
      citations, name `/s:teach <change> Q<n>` as the correction path, and
      record every consultation for the emitted ledger — each entry carrying
      `**Answered by:** ORACLE` or `**Answered by:** USER` directly above
      its answer, with `INSUFFICIENT` entries holding the user's typed
      resolution and `Queued:` slug. In the
      enrichment loop section, state that enrichment-time consultations
      append to the installed plan's existing section, continuing the
      numbering.
- [x] 4.2 [P3] [req: plan-qa-ledger] In
      `plugins/s/skills/plan/references/emission.md`, add a
      "## Questions and answers" authoring subsection after the `plan.md`
      guidance: the full entry grammar, a worked two-entry example (one
      `ANSWER` with `**Answered by:** ORACLE`, one `INSUFFICIENT` with
      `**Answered by:** USER`, the user's resolution, and its `Queued:`
      slug), the no-consultations-no-section rule, and the phrasing rule that
      entries must avoid the context gate's placeholder and open-question
      marker scans.
- [x] 4.3 [P3] [req: oracle-resolution-visibility] In
      `plugins/s/skills/plan/references/dialogue.md`, update the two spots
      that report oracle-settled decisions (the fact/decision-test routing
      paragraph and the context-brief bullet) to use the `Q<n>` reference
      shape from 4.1.

## 5. Teach skill

- [x] 5.1 [P3] [req: teach-qa-reference] In `plugins/s/skills/teach/SKILL.md`,
      add a "Ledger-entry reference mode" section before the sweep steps: an
      argument matching `<change> Q<n>` bypasses the sweep — resolve via
      `cat change` (planned or completed), print the entry in full, interview
      for the corrected standing position, then run the existing staged wiki
      emit updating the `**Cited:**` page when one exists, preserving the
      correction verbatim as a dated `sources/` file, and draining the
      `**Queued:**` block when still queued; unresolvable change or entry →
      report and stop. State that the sweep's argument handling is otherwise
      unchanged.

## 6. Ship hygiene

- [x] 6.1 [P3] [req: *] Bump the version in
      `plugins/s/.claude-plugin/plugin.json` (patch bump), per the
      plugin-cache-snapshot rule in `AGENTS.md`.
- [x] 6.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests -v` from the repo root (the exact `ci`
      invocation) and confirm the whole stdlib-only suite passes with no
      `textual` installed.
