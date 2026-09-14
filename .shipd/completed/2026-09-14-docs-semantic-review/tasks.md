# docs-semantic-review

- [x] 1.1 [P1] [req: semantic-review-doc] Verify `docs/semantic-review.md` against every claim its requirement makes, reading the live sources rather than trusting the prose. Confirm the subcommand list matches the `Subcommands:` line in `plugins/s/skills/review/SKILL.md`; the five risk-lens triggers match `### 5b. Risk lenses` there; the severity tiers and the exposure floor match the `**Severity rubric.**` block; and the suppression rule matches `plugins/s/skills/review/references/posting.md`. Report any claim the sources do not support — do not edit the doc to match a wrong source, and do not edit a source to match the doc.
- [x] 1.2 [P1] [req: semantic-review-doc] Verify the mechanical properties: `wc -l docs/semantic-review.md` reports 100 or fewer; its first line is `<!-- doc-type: concept -->`; it contains exactly one ```` ```mermaid ```` fence; and it names no command flag and no JSON field. Report each measurement.
- [x] 2.1 [P2] [req: semantic-review-doc] Confirm `docs/copilot-review.md`'s `/s:review` entry links to `semantic-review.md` and that the file still links to `copilot-review-reference.md`, which its own requirement pins. Confirm the file is 150 lines or fewer, the how-to cap.
- [x] 2.2 [P2] [req: *] Run `python3 plugins/s/skills/document/scripts/docs_lint.py docs/semantic-review.md docs/copilot-review.md` and confirm it exits `0`. Then run it over every file under `docs/` and confirm no file regressed. Report both results.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 65 | 24.6k |
| (no tool) | 0 | 4.3k |
| Write | 3 | 3.5k |
| Read | 14 | 2.2k |
| Agent | 3 | 1.2k |
| AskUserQuestion | 1 | 617 |
| **Total** | 86 | 36.3k |
