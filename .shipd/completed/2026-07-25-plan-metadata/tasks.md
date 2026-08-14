# Tasks — plan-metadata

## 1. Metadata parsing and lint validation

- [x] 1.1 [req: plan-header-metadata-lines, plan-metadata-validation] Extend
      `plugins/s/skills/build/tests/test_spec_lint.py` with header-metadata
      cases: a metadata-free plan still lints clean; `Profile:`/`Epic:`/
      `Initiative:`/`Theme:` lines after `Status:` lint clean; an unrecognized
      key (`Them: reliability`) errors; `Profile: quick` errors; a non-kebab
      value (`Theme: Not Kebab`) errors; `Epic:` plus `Initiative:` together
      errors. Run the file and observe the new tests fail.
- [x] 1.2 [req: plan-header-metadata-lines] In
      `plugins/s/skills/build/scripts/spec_common.py`, add
      `METADATA_KEYS = ("Profile", "Epic", "Initiative", "Theme")`,
      `PROFILES = ("full", "lite")`, and `parse_plan_metadata(text)` returning
      the ordered key→value pairs from the contiguous `<Key>: <value>` block
      immediately after the `Status:` line (ended by the first blank line or
      heading), including unrecognized keys so callers can report them. Add
      unit tests for the parser in
      `plugins/s/skills/build/tests/test_spec_common.py`.
- [x] 1.3 [req: plan-metadata-validation, plan-profile-values, initiative-attaches-through-epic] In
      `plugins/s/skills/build/scripts/spec_lint.py`, add
      `check_plan_metadata(root, change, errors)` wired into `lint_change`
      beside `check_plan_header`, enforcing: recognized keys only, kebab-case
      values, `Profile` in `PROFILES`, and the `Epic:`/`Initiative:`
      exclusivity (error text points at the epic as the attach point).
      Confirm the 1.1 tests pass.

## 2. Theme vocabulary config

- [x] 2.1 [req: theme-vocabulary-config] Add tests in
      `plugins/s/skills/build/tests/test_spec_lint.py`: with an
      `am/config.json` fixture declaring `valid_themes: ["reliability"]`, a
      plan with `Theme: speed` errors and `Theme: reliability` passes; with no
      config file, any kebab-case theme passes; with a malformed
      `am/config.json`, lint errors naming the file. Observe them fail.
- [x] 2.2 [req: theme-vocabulary-config] In
      `plugins/s/skills/build/scripts/spec_common.py`, add
      `load_config(root)` returning the parsed `am/config.json` dict (`{}`
      when absent, raising a clear error on malformed JSON); use it in
      `check_plan_metadata` in
      `plugins/s/skills/build/scripts/spec_lint.py` to validate `Theme:`
      against a non-empty `valid_themes`. Confirm the 2.1 tests pass.
- [x] 2.3 [req: theme-vocabulary-config] Create `am/config.json` at the repo
      root with an initial vocabulary:
      `{"valid_themes": ["developer-experience", "reliability", "spec-engine"]}`.

## 3. Status CLI preservation and display

- [x] 3.1 [req: metadata-preserving-status-writes] Add tests in
      `plugins/s/skills/build/tests/test_spec_status.py`: `set-status` on a
      plan carrying `Theme: reliability` after `Status:` rewrites only the
      `Status:` line and leaves the metadata byte-for-byte; `show` output
      includes `Profile: lite` and `Theme: reliability` when the plan carries
      them. Run and observe the `show` test fail.
- [x] 3.2 [req: metadata-preserving-status-writes] In
      `plugins/s/skills/build/scripts/spec_status.py`, extend the `show`
      verb to print the plan's recognized metadata lines (via
      `spec_common.parse_plan_metadata`) alongside status and task progress.
      Confirm the 3.1 tests pass.

## 4. Documentation and emission guidance

- [x] 4.1 [req: plan-header-metadata-lines, plan-profile-values, initiative-attaches-through-epic, theme-vocabulary-config] Document the
      metadata grammar in `am/README.md`: the header block shape after
      `Status:`, the four keys, `full`/`lite` profile semantics (lite is
      content-relaxation only; artifact set unchanged), the
      initiative-through-epic rule, and `am/config.json` with `valid_themes`.
- [x] 4.2 [req: metadata-aware-emission] Update
      `plugins/s/skills/plan/references/emission.md`: when the request
      supplies a profile, theme, epic, or initiative, emit the matching
      metadata line (honoring the initiative-through-epic rule); otherwise
      emit the bare title + `Status:` header; note that `Profile: lite`
      permits brief sections and optional test-first ordering.

## 5. Verification

- [x] 5.1 [req: *] Run the full engine test suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      `spec_lint.py` across the master library and this change; everything
      green.
