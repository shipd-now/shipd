# Tasks — epic-layer

## 1. Epic parsing and lint validation

- [x] 1.1 [req: epic-artifact-layout, epic-header-metadata, epic-structural-validation] Add
      failing tests in `plugins/s/skills/build/tests/test_spec_lint.py`
      (fixtures built in temp roots): a conforming epic passes library lint
      and `--epic` mode; missing `## Changes` section errors; status
      `verified` errors; rating `huge` errors; non-kebab or duplicate stub
      slug errors; `Profile: lite` on an epic errors as unrecognized;
      `Theme:` outside a declared `valid_themes` errors; a repo without
      `am/epics/` lints exactly as today. Run and observe the new tests fail.
- [x] 1.2 [req: epic-artifact-layout, epic-header-metadata] In
      `plugins/s/skills/build/scripts/spec_common.py`, add
      `EPIC_STATUSES = ("draft", "ready", "active", "complete")`,
      `EPIC_METADATA_KEYS = ("Theme", "Initiative")`, and
      `parse_epic_changes(text)` returning the `## Changes` stub-table rows
      as (slug, description, ratings) with the six-column header check, per
      the plan's Implementation. Add parser unit tests in
      `plugins/s/skills/build/tests/test_spec_common.py`.
- [x] 1.3 [req: epic-structural-validation, epic-artifact-layout, epic-header-metadata] In
      `plugins/s/skills/build/scripts/spec_lint.py`, add
      `lint_epic(root, slug, errors, warnings)` enforcing header, status
      vocabulary, metadata keys/values (theme vocabulary included), the three
      required sections, and the stub-table rules; walk `am/epics/*/` from
      `lint_library`; add the `--epic <slug>` CLI mode. Confirm the 1.1 tests
      pass.
- [x] 1.4 [req: epic-reference-resolution] Add failing tests, then extend
      `check_plan_metadata` (or a sibling check) in
      `plugins/s/skills/build/scripts/spec_lint.py` so change lint errors on
      an `Epic:` slug with no `am/epics/<slug>/epic.md` and warns when the
      resolved epic's stub table lacks the change's slug. Tests in
      `plugins/s/skills/build/tests/test_spec_lint.py` cover: dangling
      reference errors; missing stub row warns but exits zero; listed member
      passes silently.

## 2. Epic status verbs

- [x] 2.1 [req: epic-status-verbs] Add failing tests in
      `plugins/s/skills/build/tests/test_spec_status.py` for the three new
      verbs: `epic-show` lists status, metadata, and per-member states
      (`archived` via `am/completed/*-<slug>/`, plan status via
      `am/planned/<slug>/`, else `unplanned`); `epic-sync` derives `ready`
      (nothing started), `active` (one member active or archived),
      `complete` (all archived), and never touches `draft`;
      `epic-set-status ready` on a structurally invalid epic writes nothing,
      prints `Refused: `, exits 3; an invalid status value exits 1.
- [x] 2.2 [req: epic-status-verbs] Implement `epic-show`, `epic-sync`, and
      `epic-set-status` in `plugins/s/skills/build/scripts/spec_status.py`
      per the plan's derivation rules, reusing `spec_common` parsing and the
      existing `Refused: `/exit-3 guard convention. Confirm the 2.1 tests
      pass.

## 3. Skill, docs, and version bump

- [x] 3.1 [P3] [req: epic-interview-skill] Author
      `plugins/s/skills/epic/SKILL.md`: frontmatter (name `epic`,
      description with trigger phrases), codebase-first investigation, one
      batched AskUserQuestion round, Decisions/Design capture, stub-table
      decomposition with complexity ratings, emission at `Status: draft`,
      lint via `spec_lint.py --epic <slug>`, promotion to `ready` via
      `epic-set-status` on approval, worktree `epic-<slug>` + auto-merge PR
      shipping, and the rule that member changes are planned later via
      `/s:plan` (never created by this skill). Model it on the structure of
      `plugins/s/skills/plan/SKILL.md`.
- [x] 3.2 [P3] [req: epic-artifact-layout, epic-header-metadata, epic-reference-resolution] Document
      the epic grammar in `am/README.md`: the `am/epics/<slug>/epic.md`
      layout, header + metadata keys, required sections, the stub table with
      rating vocabulary, the epic status stages, and the membership
      warning/slug-uniqueness caveat from the plan's Risks.
- [x] 3.3 [P3] [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      `0.1.7` → `0.1.8`.

## 4. Verification

- [x] 4.1 [req: *] Run the full engine test suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`),
      `python3 plugins/s/skills/build/scripts/spec_lint.py epic-layer`, and
      library lint; everything green.
