## 1. Cover the manifest shapes an exact-name set cannot

- [x] 1.1 [req: cohort-grouping] Confirm the starting point: `python3 -m
      unittest discover -s plugins/s/skills/review/tests -v` is green
      (237 tests on v0.6.258).
- [x] 1.2 [req: cohort-grouping] In
      `plugins/s/skills/review/scripts/semdiff.py`, extend
      `MANIFEST_BASENAMES` with the exact names benchy-cf listed — the C#
      props and packages files, the Swift package and resolved files, the
      Elixir mix pair, the Dart pubspec pair, and the Python uv lock — plus
      the same-family completions named in `plan.md`'s Implementation
      section (Go workspace files, the iOS Podfile pair, the Scala build
      file).
- [x] 1.3 [req: cohort-grouping] Add a `MANIFEST_SUFFIXES` tuple for the
      project-named shapes (the C#, F# and VB project files, the gemspec,
      the nuspec, the Cabal file), and an `_is_manifest(base)` helper
      carrying all three match shapes — exact name, suffix, and the
      `requirements*.txt` family — with a docstring naming why there are
      three. Point the `contracts` rule in `COHORT_RULES` at the helper.
- [x] 1.4 [req: cohort-grouping] Verify directly against `COHORT_RULES`
      that every newly covered shape reaches the contracts cohort and that
      an api route module, a frontend component, a plain source file and a
      readme do not.

## 2. Pin both directions in tests

- [x] 2.1 [req: cohort-grouping] Add
      `test_manifests_whose_name_varies_are_matched_too` to
      `plugins/s/skills/review/tests/test_semdiff_files_context.py`,
      covering the project-named shapes and the newly added exact names,
      with a docstring recording that the benchmark's test set carries C#
      and Swift projects so these shapes are load-bearing.
- [x] 2.2 [req: cohort-grouping] Add
      `test_non_manifests_keep_their_cohorts`, asserting the api, frontend,
      test and top-level fixture paths stay out of contracts — the
      over-capture risk a suffix list and a prefix rule introduce and the
      exact-name set did not have.
- [x] 2.3 [req: cohort-grouping] Run `python3 -m unittest
      plugins.s.skills.review.tests.test_semdiff_files_context -v` and
      confirm all five tests pass.

## 3. Version and verification

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json`'s `version`
      from `0.6.258` to `0.6.259`.
- [x] 3.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` (expect 239), `python3 -m unittest
      discover -s plugins/s/skills/build/tests -v`, and `python3
      plugins/s/skills/build/scripts/spec_lint.py` (both the full lint and
      `spec_lint.py review-manifest-coverage`), confirming every suite and
      both lints pass.
