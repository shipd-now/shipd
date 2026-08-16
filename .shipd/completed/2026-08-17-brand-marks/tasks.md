## 1. Icon and docs brand

- [x] 1.1 [P1] [req: readme-brand-marks] Create repo-root `icon.svg` with exactly the
      SVG source given in plan.md's `## Implementation` ("Icon source").
- [x] 1.2 [P1] [req: readme-brand-marks] In `README.md`: insert
      `<img src="icon.svg" align="right" width="160" alt="☕ shipd">` between the
      fenced ASCII banner and the intro paragraph, and change the intro's
      `**shipd**` to `☕ **shipd**`. The fenced banner stays the first content.
- [x] 1.3 [P1] [req: readme-brand-marks] In `docs/what-is-shipd.md`: change the H1 to
      `# ☕ What is shipd?` and the lead `**shipd**` to `☕ **shipd**`.

## 2. Review summary brand line

- [x] 2.1 [P2] [req: summary-brand-mark] In
      `plugins/s/skills/review/tests/test_review_gate.py`, add a test asserting
      `render_summary(...)`'s output carries `**☕ shipd** semantic review` as
      the first non-blank line after the `<!-- am-semantic-review -->` marker,
      before the `## Findings:` header. Run
      `python3 -m unittest discover -s plugins/s/skills/review/tests` and
      observe the new test fail.
- [x] 2.2 [P3] [req: summary-brand-mark] In
      `plugins/s/skills/review/scripts/review_gate.py` `render_summary`, emit
      the brand line `**☕ shipd** semantic review` between the marker and the
      verdict header. Re-run the review suite; all tests pass.
- [x] 2.3 [P3] [req: summary-brand-mark] In `plugins/s/skills/review/SKILL.md`,
      update the summary-comment format description (the `## Findings:` header
      contract, currently around lines 140–146) to name the preceding
      `**☕ shipd** semantic review` brand line.

## 3. Board TUI brand mark

- [x] 3.1 [P2] [req: board-brand-mark] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, extend the
      header-bar test (the `#brand` query assertion near line 943) to assert the
      brand Static's content starts with `☕ ` before `shipd`. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests_textual`
      and observe it fail.
- [x] 3.2 [P3] [req: board-brand-mark] In
      `plugins/s/skills/build/scripts/dashboard.py`, change the header-bar brand
      Static (near line 3695) to
      `"☕ [$accent bold]shipd[/] [$fg-muted]delivery board[/]"`. Re-run the
      textual suite; all tests pass.

## 4. Installer brand mark

- [x] 4.1 [P2] [req: installer-brand-mark] In
      `plugins/s/skills/build/tests/test_install.py`, extend the fresh-install
      success test to assert stdout contains
      `Installed the ☕ shipd launcher at `. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      observe it fail.
- [x] 4.2 [P3] [req: installer-brand-mark] In `install.sh`, change the completion
      line to `Installed the ☕ shipd launcher at $LAUNCHER`. Re-run the build
      test suite; all tests pass.

## 5. Version bump and verification

- [x] 5.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      `0.6.123` → `0.6.124` (plugins/s content changed in this change).
- [x] 5.2 [req: *] Run all three suites — build tests, `tests_textual`, review
      tests — and confirm every one passes.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 134 | 35.4k |
| (no tool) | 0 | 7.6k |
| Read | 42 | 7.2k |
| Edit | 14 | 5.7k |
| Agent | 5 | 2.1k |
| ToolSearch | 5 | 1.4k |
| Write | 2 | 1.1k |
| SendMessage | 1 | 497 |
| Monitor | 1 | 491 |
| TaskStop | 2 | 114 |
| **Total** | 206 | 61.7k |
