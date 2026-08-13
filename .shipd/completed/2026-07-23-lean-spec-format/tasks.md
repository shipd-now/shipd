# lean-spec-format — tasks

## 1. Format docs and constitution

- [x] 1.1 [P1] Rewrite the change layout in `am/spec/README.md`: replace
      `proposal.md`/`design.md` with a single `plan.md` in the on-disk tree,
      document the plan header (`# <change>`, `Status:`) and the required
      `## Idea` / `## Implementation` sections, and keep the delta grammar
      sections unchanged.
- [x] 1.2 [P2] Add an "EARS notation" section to `am/spec/README.md` documenting
      the five patterns (ubiquitous, When, While, If/Then, Where) with
      one-line sentence templates, marked as recommended phrasing for
      SHALL/MUST statements, not lint-enforced.
- [x] 1.3 [P3] Add a context-economy note to `am/spec/README.md`: `plan.md` and
      each delta spec should stay under ~2,000 tokens; the linter warns above
      that budget.
- [x] 1.4 [P1] Create `am/spec/constitution.md` with this repo's rules: engine
      scripts are stdlib-only Python 3; `statusline.sh` stays
      POSIX-compatible; every engine change carries tests in
      `plugins/s/skills/build/tests/`; after editing `plugins/s/`, refresh
      the plugin snapshot (`claude plugin update s@shipd`); archived
      changes are immutable. Note at the top that the file is optional and
      binding on plan/build when present.

## 2. Engine cutover

- [x] 2.1 [P1] In `plugins/s/skills/build/scripts/spec_lint.py`, rename
      `check_proposal_header` to `check_plan_header`, point it at `plan.md`,
      and add errors for a missing `## Idea` or `## Implementation` level-2
      section; update all error-message wording from proposal to plan.
- [x] 2.2 [P2] In `spec_lint.py`, add a warning channel (collected separately,
      printed as `WARNING: ...` to stderr, exit code unaffected) and emit a
      context-economy warning when `plan.md` or a delta spec exceeds
      `len(text) / 4 > 2000`, naming the file and suggesting decomposition.
- [x] 2.3 [P1] In `plugins/s/skills/build/scripts/spec_status.py`, rename
      `_proposal_path` to `_plan_path` returning `plan.md`, and update the
      docstrings and error messages (`plan.md not found ...`) accordingly;
      status read/write and guard logic are otherwise unchanged.
- [x] 2.4 [P1] In `plugins/s/integrations/statusline.sh`, read the `Status:` line
      from `$change_dir/plan.md` instead of `proposal.md` (comment included);
      task counting from `tasks.md` is unchanged.

## 3. Tests and fixtures

- [x] 3.1 [P1] In `plugins/s/skills/build/tests/fixtures/sample/am/spec/changes/sample-change/`,
      merge `proposal.md` and `design.md` into a `plan.md` with the header and
      both required sections, and delete the two old files.
- [x] 3.2 [P3] Update `plugins/s/skills/build/tests/test_spec_lint.py` for the
      plan header: rename/adjust existing proposal-header tests to `plan.md`,
      and add cases for a missing `## Idea` section, a missing
      `## Implementation` section, and the context-economy warning (oversized
      `plan.md` → warning on stderr, exit 0).
- [x] 3.3 [P2] Update `plugins/s/skills/build/tests/test_spec_status.py` to
      create/read `plan.md` in its temp changes and assert the new error
      wording.
- [x] 3.4 [P2] Update `plugins/s/skills/build/tests/test_statusline.py` fixtures
      to write `plan.md` for the status line.
- [x] 3.5 [P2] Check `plugins/s/skills/build/tests/test_spec_merge.py` for
      references to the sample change's `proposal.md`/`design.md` and update
      any to `plan.md`; merge behavior itself is unchanged.

## 4. Skill and prompt updates

- [x] 4.1 [P1] Rewrite `plugins/s/skills/plan/references/emission.md`: directory
      layout (`plan.md`, `tasks.md`, `specs/`), a worked `plan.md` example
      with the header and `## Idea` / `## Implementation` sections, the EARS
      phrasing recommendation for delta requirements, the ~2,000-token
      budget, and a note to load `am/spec/constitution.md` when present.
      Keep the delta-spec and tasks sections (task discipline, `base:`
      hashes) as they are, retitled where they say proposal/design.
- [x] 4.2 [P1] In `plugins/s/skills/plan/SKILL.md`, update the artifact wording
      (summary step and any proposal/design mentions) to `plan.md` +
      `tasks.md` + deltas.
- [x] 4.3 [P1] In `plugins/s/skills/build/SKILL.md`, update the Phase 1 artifact
      list (produce `plan.md` instead of `proposal.md` + `design.md`), the
      Phase 5 verify wording, and add loading `am/spec/constitution.md` (when
      present) to the Phase 0 context gate.
- [x] 4.4 [P1] In `plugins/s/skills/build/references/teammate-prompt.md`, point
      the required reading at `am/spec/changes/<change-name>/plan.md` (Idea
      for why/what, Implementation for binding decisions) and
      `am/spec/constitution.md` when present, replacing the proposal/design
      bullets.

## 5. Cutover hygiene

- [x] 5.1 [P3] Update the root `README.md` spec-engine section: the tree at lines
      ~33-35 and the "full-ceremony artifact set" prose become the lean
      `plan.md` + `tasks.md` set; mention the constitution file.
- [x] 5.2 Convert this change's own directory: merge
      `am/spec/changes/lean-spec-format/proposal.md` and `design.md` into
      `plan.md` (Idea = proposal body, Implementation = design decisions,
      keeping the `# lean-spec-format` title and current `Status:` line) and
      delete the two old files, so post-cutover lint passes on this change.
- [x] 5.3 Run the full test suite
      (`python3 -m pytest plugins/s/skills/build/tests/`) and
      `python3 plugins/s/skills/build/scripts/spec_lint.py lean-spec-format`
      plus a master-library lint, all green.
- [x] 5.4 Refresh the plugin snapshot (`claude plugin update s@shipd`) so
      the updated skills load in the next session.
