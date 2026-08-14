## 1. Guarded CLI

- [x] 1.1 Rework `plugins/s/skills/build/scripts/spec_status.py`: replace the
      `set` verb with `set-status <status> [change] [--force]` enforcing the
      design.md D2 guard matrix (importing `lint_change` from `spec_lint`,
      same-directory sibling import); add `validate [change]` and bare
      `status [change]` verbs; implement the D3 refusal contract
      (`Refused: ` stderr lines with concrete counts/errors, exit 3; errors
      stay exit 1, usage 2). Keep `use`/`current`/`show`/`sync` unchanged.

## 2. Derived updates

- [x] 2.1 [P2] Update `plugins/s/skills/build/tests/test_spec_status.py`:
      rename `set` cases to `set-status`, and add guard coverage — complete
      refused with open tasks (exit 3, `Refused: ` on stderr, file
      unchanged), ready refused on a structurally invalid change, force
      bypasses guards (exit 0, file written), force with an invalid value
      still errors (exit 1), draft target needs no guards, `validate` on
      valid and invalid fixtures (exit 0/non-zero), and `status` printing the
      bare value and `?`.
- [x] 2.2 [P2] Create `plugins/s/skills/status/SKILL.md` (the `/s:status`
      skill) implementing design.md D4 exactly: frontmatter name/description,
      the three commands (`status`, `validate`, `set-status <status>`),
      argument-to-verb mapping with the selected-change default, the
      exit-code-3 → AskUserQuestion override flow ("Override anyway" /
      "Leave unchanged", never `--force` uninvited), and error reporting for
      exit 1. Follow the tone/structure of the existing plan SKILL.md.
- [x] 2.3 [P2] Update the pipeline call sites from `set` to `set-status`:
      `plugins/s/skills/build/SKILL.md` (Phase 2 `set ready`, Phase 3
      `set active`, Phase 5 `set verified`) and
      `plugins/s/skills/plan/SKILL.md` (hand-off `set ready`), keeping the
      surrounding wording intact and adding no `--force` anywhere.

## 3. End-to-end

- [x] 3.1 Run the full test suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and a
      live drive against this very change from the repo root: `validate
      guarded-status-skill` (expect OK), `status guarded-status-skill`
      (expect the current value), `set-status complete guarded-status-skill`
      while tasks are open (expect `Refused: ` and exit 3, status file
      unchanged), and confirm `show` still works. Report the observed
      outputs.
