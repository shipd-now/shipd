# Tasks — initiative-briefs

## 1. Brief format and lint

- [x] 1.1 [req: initiative-brief-format, initiative-lint-mode, initiative-reference-resolution] Add
      failing tests in `plugins/s/skills/build/tests/test_spec_lint.py`
      (temp-root fixtures with a fake workspace): `--initiative` passes a
      conforming brief; errors on missing `## Requirements`, status
      `pending`, unknown metadata key `Theme:`, and no-workspace (non-zero,
      "no workspace"); accepts `Project: alpha` without registry checks;
      library lint ignores a malformed unreferenced brief. Reference
      resolution: an epic and a standalone change carrying
      `Initiative: mvp-readiness` error naming the expected brief path when
      the workspace lacks the brief, pass when it exists, and emit nothing
      when no workspace is discoverable. Run and observe the new tests fail.
- [x] 1.2 [req: initiative-brief-format] In
      `plugins/s/skills/build/scripts/spec_common.py`, add
      `INITIATIVE_STATUSES = ("open", "achieved", "dropped")`,
      `BRIEF_METADATA_KEYS = ("Project",)`, and
      `initiative_brief_path(ws_root, slug)` returning
      `<ws_root>/initiatives/<slug>/brief.md`.
- [x] 1.3 [req: initiative-lint-mode, initiative-reference-resolution, initiative-brief-format] In
      `plugins/s/skills/build/scripts/spec_lint.py`, add
      `lint_initiative(ws_root, slug, errors)` (title matches slug, status
      in `INITIATIVE_STATUSES`, metadata keys within `BRIEF_METADATA_KEYS`
      with kebab values, `## Requirements` with at least one checkbox), the
      `--initiative <slug>` CLI mode (workspace resolved from `--root` via
      `find_workspace_root`, non-zero "no workspace found" when absent), and
      `check_initiative_reference` wired into both `lint_change` and
      `lint_epic` per the plan's CI-safe rule. Confirm the 1.1 tests pass.

## 2. Initiative status verbs

- [x] 2.1 [req: initiative-status-verbs] Add failing tests in
      `plugins/s/skills/build/tests/test_spec_status.py`: `initiative-show`
      prints status, metadata, `1/3` progress and requirement lines;
      `initiative-sync` derives `achieved` (all ticked, at least one) and
      `open` (any unticked), and leaves `dropped` unchanged;
      `initiative-set-status` writes a valid value and errors non-zero on
      `pending`; all three exit non-zero with a "no workspace" error when no
      workspace is discoverable.
- [x] 2.2 [req: initiative-status-verbs] Implement `initiative-show`,
      `initiative-sync`, and `initiative-set-status` in
      `plugins/s/skills/build/scripts/spec_status.py` per the plan's
      Implementation (workspace via `find_workspace_root(root)`, checkbox
      counting per the tasks.md conventions with `[~]` as unticked, status
      writes via the existing header-rewrite helper). Confirm the 2.1 tests
      pass.

## 3. Docs and version

- [x] 3.1 [P3] [req: initiative-brief-format, initiative-reference-resolution] Extend
      `am/README.md`'s Workspace section with an Initiative briefs
      subsection: the `initiatives/<slug>/brief.md` layout, header grammar
      (statuses, the `Project:` key), the requirements-as-outcomes checkbox
      rule, and the CI-safe resolution rule for `Initiative:` references.
- [x] 3.2 [P3] [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      `0.2.2` → `0.2.3`.

## 4. Verification

- [x] 4.1 [req: *] Run the full engine test suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      `python3 plugins/s/skills/build/scripts/spec_lint.py initiative-briefs`;
      everything green.
