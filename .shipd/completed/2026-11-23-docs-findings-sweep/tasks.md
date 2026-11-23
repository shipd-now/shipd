# Tasks — docs-findings-sweep

Rules for every task:

- `artefacts/replacements.md` holds every text change, grouped under one
  heading per file. "Apply the entries for X" means: for each entry under
  the heading for X, replace its `Old` text with its `New` text, once. Write
  no other word. If an `Old` text is not found exactly once, stop and report
  it; do not reword.
- "Lint" means `python3 plugins/s/skills/document/scripts/docs_lint.py <file>`
  exits 0.
- Each task in groups 2 and 3 edits its own files only, so the tasks in a
  group can run in parallel.

## 1. Tests first

- [x] 1.1 [req: readme-docs-group-links] Copy
      `artefacts/test_readme_docs_links.py`, unchanged, to
      `plugins/s/skills/build/tests/test_readme_docs_links.py`. From
      `plugins/s/skills/build/tests`, run
      `python3 -B -m unittest test_readme_docs_links` and confirm it prints
      `OK` for 8 tests. Do not edit `README.md`.
- [x] 1.2 [req: cli-self-description] Add the two methods under the
      `test_shipd_cli.py` heading of `artefacts/tests.md` to
      `plugins/s/skills/build/tests/test_shipd_cli.py`, at the place that
      heading names. From `plugins/s/skills/build/tests`, run
      `python3 -B -m unittest test_shipd_cli -k banner_calls -k docstring_serves`
      and confirm both fail.
- [x] 1.3 [req: user-configuration-file] Add the two methods under the
      `test_build_report.py` heading of `artefacts/tests.md` to
      `plugins/s/skills/build/tests/test_build_report.py`, at the place that
      heading names. From `plugins/s/skills/build/tests`, run
      `python3 -B -m unittest test_build_report` and confirm exactly one
      test fails: `test_the_build_skill_says_the_report_only_reads_the_config`.

## 2. Docs pages

- [x] 2.1 [req: docs-sweep-page-facts] Apply the entry for `docs/pr.md`.
      Lint it.
- [x] 2.2 [req: semantic-review-reference-doc] Apply the two entries for
      `docs/semantic-review-reference.md`. Lint it.
- [x] 2.3 [req: docs-sweep-page-facts] Apply the entry for
      `docs/semantic-review.md`. Lint it and confirm 100 lines or fewer.
- [x] 2.4 [req: docs-sweep-page-facts] Apply the entry for
      `docs/install.md`. Lint it and confirm `wc -l` prints 150.
- [x] 2.5 [req: docs-link-text-current-titles] Apply the entry for
      `docs/history.md`. Lint it.
- [x] 2.6 [req: docs-link-text-current-titles] Apply the entry for
      `docs/guardrails.md`. Lint it.
- [x] 2.7 [req: docs-link-text-current-titles] Apply the entry for
      `docs/copilot-review-reference.md`. Lint it and confirm `wc -l`
      prints 250.
- [x] 2.8 [req: docs-link-text-current-titles, docs-sweep-page-facts] Apply
      the five entries for `docs/room-wake-reference.md`. Lint it and
      confirm `wc -l` prints 250.
- [x] 2.9 [req: docs-sweep-page-facts] Apply the two entries for
      `docs/room-run.md`. Lint it and confirm `wc -l` prints 149.
- [x] 2.10 [req: docs-link-text-current-titles] Apply the three entries for
      `docs/tutorials/videos/09-ci-and-copilot-review.md`. Lint it.
- [x] 2.11 [req: docs-link-text-current-titles] Apply the one entry each for
      `docs/tutorials/videos/01-install-and-build.md`,
      `docs/tutorials/videos/02-plan-and-specs.md`, and
      `docs/tutorials/videos/03-worktrees-and-small-prs.md`. Lint all three.
- [x] 2.12 [req: docs-sweep-page-facts] Apply the entry for
      `docs/what-is-shipd.md`. Lint it.
- [x] 2.13 [req: docs-sweep-page-facts] Apply the entry for
      `docs/cheatsheet.md`. Lint it.
- [x] 2.14 [req: statusline-telemetry-user-docs] Apply the two entries for
      `docs/statusline-and-telemetry.md`. Lint it and confirm 150 lines or
      fewer.
- [x] 2.15 [req: docs-sweep-page-facts] Apply the two entries for
      `docs/plan.md`. Lint it and confirm `wc -l` prints 139.
- [x] 2.16 [req: docs-sweep-page-facts] Apply the entry for
      `docs/oracle.md`. Lint it and confirm `wc -l` prints 242.
- [x] 2.17 [req: docs-sweep-page-facts] Apply the entry for
      `docs/workspaces/external-stores.md`. Lint it and confirm `wc -l`
      prints 168.

## 3. Plugin texts

- [x] 3.1 [req: cli-self-description] Apply the four entries for
      `plugins/s/bin/shipd`. Run `python3 plugins/s/bin/shipd --help` and
      confirm the `harness` entry reads `the harness registry, and the
      generated` then `command files in a repo or in your home`. From
      `plugins/s/skills/build/tests`, run
      `python3 -B -m unittest test_shipd_cli -k banner -k docstring` and
      confirm `OK`.
- [x] 3.2 [req: user-configuration-file] Apply the entry for
      `plugins/s/skills/build/SKILL.md`. From
      `plugins/s/skills/build/tests`, run
      `python3 -B -m unittest test_build_report` and confirm `OK`.
- [x] 3.3 [req: *] Run `git fetch origin main`, then
      `git show origin/main:plugins/s/.claude-plugin/plugin.json` and read
      its `version`. Set `version` in `plugins/s/.claude-plugin/plugin.json`
      to that version with its last number raised by one. Change nothing
      else in the file.

## 4. Verify

- [x] 4.1 [req: core-ideas-doc] Run `grep -n "read, then" docs/core-ideas.md`
      and confirm one line names the ladder as read, then oracle, then
      human. Do not edit the page.
- [x] 4.2 [req: install-mode-docs] Run
      `grep -n "autoUpdate\|shipd update\|shipd vendor\|ln -s" README.md`
      and confirm no line matches. Run
      `grep -c "distribution vehicle\|plugin/s/bin/shipd\|/plugin marketplace add <path-to-your-checkout>\|/plugin install s@shipd" README.md`
      and confirm it prints 4. Do not edit `README.md`.
- [x] 4.3 [req: docs-link-text-current-titles] Run
      `grep -rn "Install the Copilot review gate\|\[Copilot review reference\]\|Room wake reference\|last three lines" docs --include="*.md"`
      and confirm every match sits under `docs/retros/`. Run
      `grep -rn "\[Getting started\](" docs --include="*.md"` and confirm
      every match outside `docs/retros/` links the page
      `docs/workspaces/getting-started.md`.
- [x] 4.4 [req: *] Run the CI docs lint: `python3
      plugins/s/skills/document/scripts/docs_lint.py $(find docs -name
      "*.md" -not -path "docs/retros/*")` and confirm exit 0.
- [x] 4.5 [req: *] Run each suite with `python3 -B -m unittest discover -s
      <dir>` for `plugins/s/skills/build/tests`,
      `plugins/s/skills/review/tests`, `plugins/s/skills/room/tests`,
      `plugins/s/skills/pr/tests`, and `plugins/s/skills/document/tests`.
      For each, grep the output for the `OK` or `FAILED` verdict line and
      confirm `OK`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 132 | 93.8k |
| Write | 10 | 26.9k |
| SubagentHandback | 6 | 13.2k |
| (no tool) | 0 | 2.5k |
| SendMessage | 4 | 2.2k |
| Agent | 2 | 2.0k |
| ToolSearch | 5 | 1.1k |
| Edit | 3 | 1.1k |
| AskUserQuestion | 1 | 1.0k |
| Read | 6 | 1.0k |
| Monitor | 1 | 224 |
| TaskStop | 2 | 114 |
| **Total** | 172 | 145.2k |
