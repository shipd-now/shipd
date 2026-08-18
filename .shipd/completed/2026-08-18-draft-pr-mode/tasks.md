## 1. Config key and accessor

- [x] 1.1 [req: pr-mode-key] Add tests to
      `plugins/s/skills/build/tests/test_spec_common.py`: `resolve_pr_mode`
      returns `auto` with no layer declaring the key; returns `draft` when an
      ancestor (workspace-style) layer declares `"pr-mode": "draft"` and
      resolution starts from a nested repo dir; raises `ConfigError` naming
      `pr-mode` and the accepted values on `"pr-mode": "always"`. Run them and
      observe them fail — the accessor does not exist yet.
- [x] 1.2 [req: pr-mode-key] In
      `plugins/s/skills/build/scripts/spec_common.py`, beside
      `resolve_pipeline`, add `PR_MODE_KEY = "pr-mode"` and
      `resolve_pr_mode(root)` per the plan's accessor shape (stdlib-only,
      `ConfigError` on an invalid value). Confirm the 1.1 tests pass.

## 2. Autopilot drafted outcome

- [x] 2.1 [req: pipeline-stage-execution, run-report-and-controls] Add tests
      to `plugins/s/skills/build/tests/test_autopilot.py` using the existing
      `command_fn`/driver seams: with a root config layer declaring
      `"pr-mode": "draft"`, (i) a member whose stages all pass and whose
      `gh pr view` reports an open unmerged PR resolves to outcome `drafted`
      with the PR URL; (ii) the run report carries a `drafted` bucket listing
      that member and URL, and `_summarize` renders a `drafted:` line; (iii)
      no epic-sync close-out is attempted when only drafted members exist;
      (iv) the draft-mode build stage prompt names a draft PR, not an
      auto-merging one; (v) with no `pr-mode` declared, the same unmerged-PR
      member still parks as `needs_human` at stage `merge`. Run them and
      observe them fail.
- [x] 2.2 [req: pipeline-stage-execution] In
      `plugins/s/skills/build/scripts/autopilot.py`, resolve the mode once
      per run via `sc.resolve_pr_mode(root)` in `drive_epic` and the targeted
      single-member drive, thread it into `drive_member`, and change only the
      end-of-pipeline PR resolution: draft mode + existing unmerged PR →
      `MemberResult(outcome="drafted", pr_url=url)`; no PR still parks
      `needs_human` at `merge`; the vanished-worktree paths stay unchanged.
      Update the adjacent rationale comment.
- [x] 2.3 [req: pipeline-stage-execution] In `autopilot.py`'s
      `_stage_prompt`, when the resolved mode is draft, word the `build`
      stage prompt as "open its draft PR (draft mode — do not enable
      auto-merge)" in place of "open its auto-merging PR".
- [x] 2.4 [req: run-report-and-controls] In `autopilot.py`, add a
      `"drafted": []` bucket to both report dicts (the `drive_epic` assembly
      and the targeted-drive assembly), append
      `{"member", "pr_url"}` entries on a `drafted` outcome, render
      `drafted:` lines in `_summarize`, and leave `any_merged` keyed off
      `result.merged` so drafted members never trigger the close-out.
      Confirm the 2.1 tests pass.

## 3. Build skill ship phase

- [x] 3.1 [req: ship-changes-as-prs] In `plugins/s/skills/build/SKILL.md`'s
      ship section (the `gh pr create --fill` block and the
      merge-state/watch instructions that follow), branch on the `pr-mode`
      line of `spec_status.py config-show`: in draft mode use
      `gh pr create --fill --draft`, do not run `gh pr merge --auto`, skip
      the `mergeStateStatus` read, reconciliation, PR watch, and merged
      close-out; still post the semantic-review gate and disposition loop per
      the pipeline's review entry; end reporting the draft PR's full URL and
      that merging is a human's step, leaving the worktree in place; on a
      `pr-mode` value other than `auto`/`draft`, stop before pushing and
      report the error naming `pr-mode`. Leave the epic-close and
      close-out sections' auto-merging instructions untouched.

## 4. Docs, version, verification

- [x] 4.1 [req: pr-mode-key] Document the `pr-mode` key in `README.md`'s
      configuration section (near the `autonomous-pipeline` paragraph):
      values, default, workspace-root placement, and that it governs
      change-shipping PRs only.
- [x] 4.2 [req: *] Bump the version in
      `plugins/s/.claude-plugin/plugin.json` to the next patch (0.6.135 →
      0.6.136 unless a later version has already landed on `main`).
- [x] 4.3 [req: *] Run the full stdlib suite as CI does —
      `python3 -m unittest discover -s plugins/s/skills/build/tests -v` (no
      `textual`/`pydantic` required) — and confirm it passes.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 89 | 28.9k |
| Edit | 29 | 20.7k |
| (no tool) | 0 | 7.8k |
| Read | 34 | 5.6k |
| Write | 1 | 5.4k |
| SendMessage | 1 | 1.3k |
| Agent | 2 | 851 |
| **Total** | 156 | 70.5k |
