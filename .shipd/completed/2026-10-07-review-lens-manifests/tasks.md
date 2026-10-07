## 1. Group manifests into the contracts cohort

- [x] 1.1 [req: cohort-grouping] Confirm the starting point: `python3 -m
      unittest discover -s plugins/s/skills/review/tests -v` is green and
      `wc -l plugins/s/skills/review/SKILL.md` reports 325.
- [x] 1.2 [req: cohort-grouping] In
      `plugins/s/skills/review/scripts/semdiff.py`, add a
      `MANIFEST_BASENAMES` frozenset covering `package.json` and its
      lockfiles, `go.mod`/`go.sum`, `Cargo.toml`/`Cargo.lock`,
      `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements.txt`,
      `Pipfile` and its lock, `poetry.lock`, `Gemfile` and its lock,
      `composer.json` and its lock, `pom.xml`, and the Gradle build files.
      Extend the `contracts` rule in `COHORT_RULES` to match
      `base.lower() in MANIFEST_BASENAMES` alongside its `.proto` test, with
      a comment saying why a manifest is a contract and why the match is on
      basename.
- [x] 1.3 [req: cohort-grouping] Verify the classification directly against
      `COHORT_RULES` over nine representative path strings (none of them
      files in this repo): a root package manifest, a nested one under a
      server directory, a Go module file, a Cargo manifest, a Maven POM, a
      package manifest under a test-fixtures directory, an api route
      module, a frontend component, and a plain source file. Manifests must
      reach the contracts cohort; the non-manifests must keep the cohorts
      they had.
- [x] 1.4 [req: cohort-grouping] Add
      `test_manifests_land_in_contracts` to
      `plugins/s/skills/review/tests/test_semdiff_files_context.py`,
      writing its own manifest files rather than extending the shared
      fixture (whose file count `test_cohort_grouping` asserts). Pin the
      test-fixtures-directory manifest case explicitly, with a comment that
      the contracts-first ordering is a deliberate choice.

## 2. Add the sixth risk-lens trigger

- [x] 2.1 [req: review-risk-lenses] Append a `## Packaging and dependency
      manifests` section to
      `plugins/s/skills/review/references/risk-lenses.md`, in the shape its
      five siblings use: what to look for, framed as four ordered questions
      (does a new file actually ship; does the manifest declare what the
      code imports; do manifest and lockfile agree; did a version
      constraint move); then real-finding and reflex examples drawn from
      the pg-pool misses; then the severity line naming `contract` as the
      normal category and no floor.
- [x] 2.2 [req: review-risk-lenses] In
      `plugins/s/skills/review/SKILL.md` step 5b, change "five fixed
      triggers" to "six" and add the trigger as a sixth bullet.
- [x] 2.3 [req: review-risk-lenses] In
      `plugins/s/harness/bodies/review.md` step 7, change "five triggers"
      to "six" and extend the inline list, keeping the substance inline
      since that file can read no reference.
- [x] 2.4 [req: review-risk-lenses] In
      `plugins/s/integrations/copilot/SKILL.md` step 5, do the same.
- [x] 2.5 [req: review-risk-lenses] Add
      `"packaging and dependency manifests"` to `TRIGGER_PHRASES` in
      `plugins/s/skills/review/tests/test_skill_references.py`. This is
      what enforces the trigger on all three surfaces — `_missing_triggers`
      already checks each against the tuple, so no new test is needed.
- [x] 2.6 [req: review-risk-lenses] Confirm both budgets: `wc -l
      plugins/s/skills/review/SKILL.md` under 330, rendered review body
      under 140.

## 3. Version and verification

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json`'s `version`
      from `0.6.257` to `0.6.258`.
- [x] 3.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` (expect 237 — the new cohort test
      adds one), `python3 -m unittest discover -s
      plugins/s/skills/build/tests -v`, and `python3
      plugins/s/skills/build/scripts/spec_lint.py` (both the full lint and
      `spec_lint.py review-lens-manifests`), confirming every suite and
      both lints pass.
