## 1. Clean-verdict wording

- [x] 1.1 [req: summary-clean-wording] In `plugins/s/skills/review/tests/test_review_gate.py`, add a test that `render_summary` with an empty findings list carries `No problems found.`, no `| # |` header, and no `No findings`. Run it and observe it fail.
- [x] 1.2 [req: summary-clean-wording] In `plugins/s/skills/review/scripts/review_gate.py`, add the module constant `NO_PROBLEMS = "No problems found."` above `render_summary` and render it in place of `No findings.`; confirm 1.1 passes.
- [x] 1.3 [req: summary-clean-wording, copilot-clean-wording] In `plugins/s/skills/review/tests/test_skill_references.py`, add `NoProblemsWordingTest`: `review_gate.NO_PROBLEMS` equals the sentence; `SKILL_MD` and `COPILOT_SKILL_MD` each contain `No problems found.` and `Reviewed N files, +A -D lines.` and not `No findings.`. Run it and observe it fail.
- [x] 1.4 [req: copilot-clean-wording] In `plugins/s/integrations/copilot/SKILL.md`, change the report instruction to `No findings: say \`No problems found.\` in place of the table.` and, after the sentence sanctioning the posting step's severity dots, add that the posting step closes the posted body with `Reviewed N files, +A -D lines.` and the agent must not write that line.
- [x] 1.5 [req: summary-clean-wording] In `plugins/s/skills/review/SKILL.md`, item 3 of the report shape, replace `"No findings."` with `"No problems found."` and add that `review_gate.py post` closes the summary comment with `Reviewed N files, +A -D lines.` counted from the PR's own file list; confirm 1.3 passes.

## 2. Poster footer

- [x] 2.1 [req: summary-review-footer] In `test_review_gate.py`, add `SummaryFooterTest` covering: footer is the last non-blank line for a two-file list (`Reviewed 2 files, +112 -3 lines.`); footer follows the "Additional findings" section; singular `Reviewed 1 file, +12 -3 lines.`; count-less `Reviewed 1 file.`; a `True` addition counts as zero; `None`, `[]`, and `["junk"]` render no footer; `post` with `FakeGh(files=...)` ends the summary with the footer; the folded re-post after `review_fail_times=1` keeps it. Run and observe failures.
- [x] 2.2 [req: summary-review-footer] In `review_gate.py`, add `review_footer(files)` next to `NO_PROBLEMS`: keep dict entries; return `None` when there are none; count entries whose `additions` or `deletions` pass `_line_number`; format `Reviewed %d file%s` plus `, +%d -%d lines` only when any entry carried a count; end with a period.
- [x] 2.3 [req: summary-review-footer] In `review_gate.py`, add the trailing keyword `files=None` to `render_summary`, append `["", footer]` after the "Additional findings" block when `review_footer(files)` is truthy, and pass `files` from `post` on both `render_summary` calls; confirm 2.1 passes.

## 3. Workflow footer

- [x] 3.1 [req: gate-body-footer] In `test_skill_references.py`, add `FooterParityTest` that executes `_workflow_namespace()["footer"]` against `[]`, `["junk"]`, a count-less entry, a single counted entry, a mixed three-entry list, and a bool-count entry, asserting `[]` when `review_gate.review_footer` returns `None` and `["", <line>]` otherwise, plus `[]` for `None` and a dict input. Run and observe it fail.
- [x] 3.2 [req: gate-body-footer] In `plugins/s/integrations/copilot/copilot-review-gate.yml`, in the posting step's embedded Python between `prose` and `fold`, add `footer(files)` mirroring `review_footer` using the step's `is_line`, returning `["", line]` or `[]`; change the payload body to `fold(body, prose(unverified) + footer(files))`; confirm 3.1 passes and the YAML still parses.

## 4. Verification

- [x] 4.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` to `0.6.239`, then run `python3 -m unittest discover -s plugins/s/skills/review/tests -p 'test_*.py'` and confirm it exits 0.
