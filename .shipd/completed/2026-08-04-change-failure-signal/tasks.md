# Tasks — change-failure-signal

## 1. Fixes metadata key

- [x] 1.1 [req: plan-header-metadata-lines] In
      `plugins/s/skills/build/tests/test_spec_lint.py`, add failing tests: a
      planned change whose `plan.md` header carries `Fixes: some-shipped-slug`
      (plus a second, repeated `Fixes:` line) lints clean, and a
      `Fixes: Not_Kebab` value reports the kebab-case metadata error. Run the
      tests and observe them fail.
- [x] 1.2 [req: plan-header-metadata-lines] In
      `plugins/s/skills/build/scripts/spec_common.py`, append `"Fixes"` to
      `METADATA_KEYS` and update the adjacent comment (five recognized keys;
      `Fixes` repeatable, naming a shipped change the plan remediates). Confirm
      the 1.1 tests and the existing metadata tests pass.

## 2. Failure signal collection

- [x] 2.1 [req: change-failure-signal] In
      `plugins/s/skills/build/tests/test_metrics.py`, add failing tests for
      the signal sources: `git_revert_signals` parses a
      `Revert "a: ship the widget"` subject into `{"a": [<utc iso ts>]}` from
      a fixture git history (built the way the existing `git_change_times`
      tests build theirs), excludes a `Revert "Revert "a: ..."` subject, and
      returns `{}` on a non-repository root; `collect_fix_links` reads
      `Fixes:` header lines from `completed/<date>-<slug>/plan.md` fixtures
      into a fixed-slug → [fixing slugs] map, skipping archives without the
      key.
- [x] 2.2 [req: change-failure-signal] In
      `plugins/s/skills/build/scripts/metrics.py`, add
      `git_revert_signals(root, base_ref=None)` — one `git log --format` scan
      per the `git_change_times` idiom (stdlib subprocess, stderr devnulled,
      `base_ref or "HEAD"`, any failure or non-repo → `{}`); a subject
      signals a revert when it starts `Revert "` and its quoted text does not
      itself start `Revert `, keyed by the quoted text's `<slug>:` prefix,
      values the commits' UTC ISO committer timestamps — and
      `collect_fix_links(root)` — walk `completed/` dirs matching
      `_ARCHIVE_DIR_RE`, parse each `plan.md` header with
      `sc.parse_plan_metadata`, and collect every `Fixes` pair. Confirm the
      2.1 tests pass.
- [x] 2.3 [req: change-failure-signal] In `test_metrics.py`, add failing tests
      for `collect_change_failures`: a reverted shipped change and a
      `Fixes:`-declared one each appear in `failed` with their signals
      (`{kind: "revert", ts}` / `{kind: "fix", by}`); a change carrying both
      signals counts once in `n_failed`; a revert naming a slug absent from
      the ship events is ignored; `rate == n_failed / n_shipped`; and an empty
      ship-event list yields `rate is None` without raising.
- [x] 2.4 [req: change-failure-signal] In `metrics.py`, add
      `collect_change_failures(root, ship_events, base_ref=None)` joining
      `git_revert_signals` (looked up as a module attribute at call time, so
      tests monkeypatch it) and `collect_fix_links` over the shipped slugs
      into `{rate, n_failed, n_shipped, failed: [{slug, signals}]}` sorted by
      slug. Confirm the 2.3 tests pass.

## 3. Derive and surfaces

- [x] 3.1 [req: change-failure-signal, metrics-engine] In `test_metrics.py`,
      add failing tests for the wiring: `derive` carries a `change_failures`
      block (JSON-serializable, present on an empty root with `rate` `None`);
      `summary` prints
      `change-fail rate: <pct> (post-merge: reverts + declared fixes)` beside
      the rework line and the literal n/a on an empty root; the em rollup's `## rework`
      section prints the same line; the exec rollup's `headlines` carry
      `change_fail_rate`, its rendered lines print the rate, and no failed
      slug appears anywhere in the exec block's JSON serialization or lines.
- [x] 3.2 [req: change-failure-signal, metrics-engine] In `metrics.py`, wire
      the block: `derive()` composes
      `collect_change_failures(root, ship_events)` into a `change_failures`
      key (docstring updated — the seam is now resolved);
      `render_summary_lines` adds the change-fail line after the rework line;
      `_build_exec_block` headlines gain `change_fail_rate` and
      `_rollup_exec_lines` print it; `_build_em_block` gains
      `change_fail_rate` and `_rollup_em_lines` print it under `## rework` —
      all through `_fmt_pct`. Confirm the 3.1 tests pass.

## 4. Ship

- [x] 4.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` (patch bump).
- [x] 4.2 [req: *] Run the full dependency-free suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`)
      without `textual` installed and confirm it passes.
