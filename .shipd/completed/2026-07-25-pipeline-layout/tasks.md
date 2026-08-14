## 1. The flip (atomic barrier)

- [x] 1.1 Perform the tree flip and coordinator repath as ONE task, in this
      exact order: `git mv am/spec/changes/archive am/completed` (archive out
      first), `git mv am/spec/changes am/planned`,
      `git mv am/spec/specs am/verified`,
      `git mv am/spec/README.md am/README.md`,
      `git mv am/spec/constitution.md am/constitution.md`, remove the now-empty
      `am/spec/`; then in
      `plugins/s/skills/build/scripts/claim_task.sh` change the `TASKS` and
      `LOCK` constants to `am/planned/${CHANGE}/...` and update its usage
      comments (`./am/spec` → `./am`, "am/spec tasks.md checklists" wording).

## 2. Repath tools, tests, and docs

- [x] 2.1 [P1] In `plugins/s/skills/build/scripts/spec_common.py`: repoint
      every path helper and docstring from `am/spec/specs` → `am/verified` and
      `am/spec/changes` → `am/planned`; update any archive-path helper to
      `am/completed`.
- [x] 2.2 [P1] In `plugins/s/skills/build/scripts/spec_lint.py`: update path
      resolution, docstrings, and error-message text to the new layout
      (`am/planned/<change>/`, master library `am/verified/`).
- [x] 2.3 [P1] In `plugins/s/skills/build/scripts/spec_merge.py`: merge target
      `am/verified/`, archive destination `am/completed/<date>-<change>/`
      (keep the date prefix), and message/docstring text updated accordingly.
- [x] 2.4 [P1] In `plugins/s/skills/build/scripts/spec_status.py`: resolve
      changes under `am/planned/`; `use` validates existence under
      `am/planned/` (no nested-archive exclusion needed — `am/completed/` is a
      sibling); update docstrings/messages.
- [x] 2.5 [P1] In `plugins/s/integrations/statusline.sh`: set
      `changes_dir="$workspace/am/planned"`, delete the `! -name archive`
      find-exclusion (planned/ holds only live changes), and update header
      comments; keep bash-3.2 compatibility.
- [x] 2.6 [P1] In `plugins/s/skills/build/tests/test_claim_task.py` and
      `test_statusline.py`: change every temp-fixture layout builder from
      `am/spec/changes/...` to `am/planned/...`.
- [x] 2.7 [P1] `git mv` the fixture trees under
      `plugins/s/skills/build/tests/fixtures/` from `.../am/spec/specs/...`
      to `.../am/verified/...` and `.../am/spec/changes/...` to
      `.../am/planned/...` (both `sample/` and `bad/`), and update the
      fixture-path constants in `test_spec_common.py`, `test_spec_lint.py`,
      `test_spec_merge.py`, and `test_spec_status.py`.
- [x] 2.8 [P1] In `plugins/s/skills/build/SKILL.md` and
      `plugins/s/skills/build/references/subagent-prompt.md`: replace every
      `am/spec/specs` → `am/verified`, `am/spec/changes/archive` →
      `am/completed`, `am/spec/changes` → `am/planned`,
      `am/spec/constitution.md` → `am/constitution.md`, `am/spec/README.md` →
      `am/README.md`, and bare `am/spec` layout references → `am/`.
- [x] 2.9 [P1] Apply the same path substitutions as 2.8 in
      `plugins/s/skills/plan/SKILL.md`,
      `plugins/s/skills/plan/references/emission.md` (including its directory
      layout block), and `plugins/s/skills/plan/references/readiness.md`.
- [x] 2.10 [P1] Apply the same path substitutions as 2.8 in
      `plugins/s/skills/status/SKILL.md`.
- [x] 2.11 [P1] In root `README.md` and `AGENTS.md`: update the repo-tree
      diagram and all prose paths to the new `am/` layout (planned/,
      completed/, verified/, am/README.md, am/constitution.md).
- [x] 2.12 [P1] Update the moved files' own text: in `am/README.md`, retitle
      from "am/spec — the shipd spec library" to the `am/` layout and
      rewrite its on-disk layout block and prose paths (specs→verified,
      changes→planned, archive→completed); in `am/constitution.md`, update the
      immutable-archive rule to name `am/completed/`.

## 3. Verify (barrier)

- [x] 3.1 Run the full suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and fix
      nothing-else; then `grep -rn "am/spec" .` from the repo root and confirm
      the only remaining hits are inside `am/completed/` and `openspec/`
      (frozen history); then pipe session JSON with the repo root as
      `workspace.current_dir` into `plugins/s/integrations/statusline.sh` and
      confirm it renders `☕ pipeline-layout · active · <n>/<total>`; finally
      run `python3 plugins/s/skills/build/scripts/spec_lint.py
      pipeline-layout` and confirm exit 0 against the new layout.
