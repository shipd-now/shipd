## 1. Pin difftastic in the engine installer

- [x] 1.1 [req: doctor-provisioning] In
      `plugins/s/skills/review/tests/test_semdiff_doctor.py`, add a test
      asserting the release-binary installer's URL names a pinned version and
      does not contain `releases/latest/download/`. Run it and observe it
      fail.
- [x] 1.2 [req: doctor-provisioning] In
      `plugins/s/skills/review/scripts/semdiff.py`, add a module-level
      `DIFFT_VERSION = "0.71.0"` constant and rewrite the `install_difft` URL
      (line 131) to
      `https://github.com/Wilfred/difftastic/releases/download/{DIFFT_VERSION}/difft-{DIFFT_VERSION}-{target}.tar.gz`.
      Confirm the test from 1.1 passes.

## 2. Make a missing difftastic fail the diff

- [x] 2.1 [req: text-fallback] In
      `plugins/s/skills/review/tests/test_semdiff_diff.py`, add a test running
      `semdiff diff` with `difft` absent from `PATH`, asserting a non-zero
      exit, no stdout JSON, and a stderr message naming the install remedy.
      Add a second test asserting that a per-file difft parse failure still
      exits zero and stamps `engine: "text"` on that file. Run both and
      observe the first fail.
- [x] 2.2 [req: text-fallback] In
      `plugins/s/skills/review/scripts/semdiff.py`, make the `diff`
      subcommand call `die()` when `have("difft")` is false, naming
      `semdiff doctor --fix` as the remedy. Leave the per-file
      `"fallback"` retry in `_difft_entry` (line 393) and the text engine
      (lines 421-573) untouched. Confirm both tests from 2.1 pass.
- [x] 2.3 [req: doctor-provisioning] In the same file, move `difft` from the
      `recommended` tier to `required` in the doctor's tool table (line 77),
      so `semdiff doctor` exits non-zero when it is missing. Update the
      `recommended`/`required` explanatory comment at line 72.
- [x] 2.4 [req: review-difft-autofix] In
      `plugins/s/skills/review/tests/test_skill_references.py`, add a test
      asserting `plugins/s/skills/review/SKILL.md`'s `## Degradation` section
      no longer instructs the reviewer to complete on the text engine, and
      does instruct it to stop. Run it and observe it fail.
- [x] 2.5 [req: review-difft-autofix] In `plugins/s/skills/review/SKILL.md`,
      rewrite the `## Degradation` section: a missing `difft` stops the
      review after the one `doctor --fix` attempt, reporting that difftastic
      is required, the manual install hint, and that no verdict was
      produced. Keep the at-most-once installer rule. Keep the
      could-not-verify reporting for the per-file parse-failure retry, which
      still degrades. Confirm the test from 2.4 passes.

## 3. Install difftastic in CI

- [x] 3.1 [req: review-test-coverage] In `.github/workflows/ci.yml`, add a
      step before "Run review test suite" that installs difftastic at the
      pinned version, mirroring the gate template's install step.
- [x] 3.2 [req: review-test-coverage] Run
      `python3 -m unittest discover -s plugins/s/skills/review/tests` with
      difftastic present and repair every failure among the five previously
      skipped `@unittest.skipUnless(HAVE_DIFFT, …)` tests. They have never
      run in the pipeline, so treat a failure as this task's work.
- [x] 3.3 [req: review-test-coverage] In
      `plugins/s/skills/review/tests/test_semdiff_diff.py`, remove the
      `SummarizeChunksLineNumberTest` class comment's claim that "CI never
      installs difftastic", keeping the test itself.

## 4. Pin the gate's difftastic download

- [x] 4.1 [req: gate-workflow-template] In
      `plugins/s/skills/review/tests/test_review_gate.py`, add a test
      asserting `plugins/s/integrations/copilot/copilot-review-gate.yml`
      names a pinned difftastic version and no
      `releases/latest/download/`. Run it and observe it fail.
- [x] 4.2 [req: gate-workflow-template] In
      `plugins/s/integrations/copilot/copilot-review-gate.yml`, replace the
      unversioned fetch at line 211 with a `difft_version=0.71.0` assignment
      and the versioned URL. The `curl -f` already fails the step on a bad
      download; add a comment recording that the guard is deliberate, beside
      the existing empty-archive check. Confirm 4.1 passes.

## 5. Enforce the pinned reviewer instructions

- [x] 5.1 [req: gate-workflow-template] In
      `plugins/s/skills/review/tests/test_review_gate.py`, add a test
      asserting the workflow writes the base ref's skill content over
      `$skill_path` in the checkout, and that the reviewer invocation carries
      `--add-dir`. Run it and observe it fail.
- [x] 5.2 [req: gate-workflow-template] In the gate workflow, change the
      materialization at lines 318-331 so the base ref's copy is written over
      `$skill_path` in the checkout as well as to `$instructions_file`. Leave
      the `base_commit` resolution and its two hard failures (lines 308-322)
      unchanged.
- [x] 5.3 [req: gate-workflow-template] In the same file, add
      `--add-dir "${RUNNER_TEMP:-.}"` to the `copilot -p` invocation at line
      363, and record in the adjacent comment that `--allow-all-tools`
      authorizes tool use without widening the path sandbox. Confirm 5.1
      passes.

## 6. Scan backwards for the verdict

- [x] 6.1 [req: gate-workflow-template] In
      `plugins/s/skills/review/tests/test_review_gate.py`, add tests for the
      classifier over these bodies: a marker followed by reviewer narration
      (parses), a marker quoted mid-sentence only (no verdict), a marker
      inside a `│`-prefixed transcript line (no verdict), a marker with text
      appended (no verdict), no marker (no verdict), `fix-required` last with
      `ship-it` earlier (fix-required), a marker with trailing spaces
      (parses), and an indented marker (parses). Run them and observe the
      narration case fail.
- [x] 6.2 [req: gate-workflow-template] In the gate workflow's "Classify the
      reviewed text and post the verdict" step (lines 509-589), replace the
      last-non-empty-line rule with a backwards scan over at most the final
      200 lines, taking the last line equal to a marker. Use `%%` prefix
      removal for the trailing-whitespace test, never `##`. Use pure bash
      with no pipe into `grep`, preserving the documented SIGPIPE reasoning.
      Confirm every test from 6.1 passes.
- [x] 6.3 [req: gate-workflow-template] In the same step's comment block,
      replace the last-non-empty-line rationale with the backwards-scan one,
      and state the residual window: a bare marker alone on its own line in
      trailing narration is still read as the verdict.

## 7. Documentation

- [x] 7.1 [req: difft-required-docs] In `docs/semantic-review.md`, rewrite the
      `## When a tool is missing` section (lines 86-91): a review without
      `difft` stops rather than degrading, the engine is required, and a
      linter that crashes or times out still reports as failed with the
      review completing. State the behaviour as it is; name no change, no
      previous behaviour, and no migration. The file is exactly 100 lines,
      its concept cap, so the rewrite must not grow it.
- [x] 7.2 [req: difft-required-docs] In `docs/copilot-review-reference.md`,
      rewrite the optional-tools bullet (lines 246-248): `difft` is required
      and its absence stops the review; `ripgrep` stays optional and still
      falls back to `git grep`. State it as current fact only. The file is
      exactly 250 lines, its reference cap, so the rewrite must not grow it.
- [x] 7.3 [req: doctor-verb] In `plugins/s/bin/shipd`, change the `difft`
      warning detail so it names the semantic review being unable to run as
      the affected surface, rather than a text-engine degradation. The check
      stays a warning; only its wording changes.
- [x] 7.4 [req: doctor-verb] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, update the `difft`
      warning-detail assertion to match the new wording, and confirm the
      build suite passes.
- [x] 7.5 [req: difft-required-docs] Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/semantic-review.md docs/copilot-review-reference.md`
      and fix every finding until it exits clean.
- [x] 7.6 [req: difft-required-docs] Grep `docs/` and
      `plugins/s/skills/review/SKILL.md` for the words `degrade`, `fallback`,
      and `text engine`, and confirm every remaining occurrence describes
      either the per-file parse-failure retry or a non-difftastic subject.
      Repair any that still claims a missing `difft` degrades a review.

## 8. Ship prerequisites

- [x] 8.1 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      to the next patch above the version the base branch carries at the
      time. Verify the bump with the engine's version guard
      (`plugins/s/skills/build/scripts/version_guard.py`), passing the base
      branch as its `--base` and `HEAD` as its `--head`; it must exit zero.

## 9. Verification

- [x] 9.1 [req: *] Run
      `python3 -m unittest discover -s plugins/s/skills/review/tests` and
      `python3 -m unittest discover -s plugins/s/skills/build/tests`, and
      confirm both pass with no test skipped for difftastic's absence.
- [x] 9.2 [req: *] Run `python3 plugins/s/skills/review/scripts/semdiff.py
      diff main HEAD` with difftastic present and confirm it emits
      `engine: "difft"`; re-run with `difft` off `PATH` and confirm a
      non-zero exit with no JSON.
