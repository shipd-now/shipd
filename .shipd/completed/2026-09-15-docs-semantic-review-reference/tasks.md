# docs-semantic-review-reference

- [x] 1.1 [P1] [req: semantic-review-reference-doc] Gather every value the reference must carry, reading each from its running source rather than from any summary, and report what you read. From `plugins/s/skills/review/references/json-output.md`: the finding object's fields, the ten `category` values in order, the `verdict` rule, and the conditions in its `## The optional suggestion object` section. From the `// lint` entry in `plugins/s/skills/build/references/shipd.config.example.json`: both members and their defaults. From the `prior` docstring in `plugins/s/skills/review/scripts/review_gate.py`: the entry fields and the four disposition classes with the rule that assigns each.
- [x] 1.2 [P1] [req: semantic-review-reference-doc] Observe `prior`'s real output so the reference describes what a reader will actually see. Run `python3 plugins/s/skills/review/scripts/review_gate.py prior 208` and `prior 205` from the repository root, and report for each: the entry count, the `disposition` values present, and whether `hash` is null or a string. Do not change any code to alter that output.
- [x] 2.1 [P2] [req: semantic-review-reference-doc] Read the shipd documentation standard at `${CLAUDE_PLUGIN_ROOT}/skills/document/references/standard.md` before writing a word, then write `docs/semantic-review-reference.md` against it. Open with `<!-- doc-type: reference -->`, a `# Semantic review reference` title, and an opening that names `semantic-review.md` as the concept guide in the shape `docs/prd-reference.md` uses. Carry three level-2 sections in this order: the `--json` payload, the `lint` configuration key, and the `prior` verb. Cover every item the delta requires, including the null-hash rule and the fact that re-posting the gate creates a new thread rather than updating the old one. Stay under 250 lines, and list values rather than narrating workflow — the concept guide owns the narrative.
- [x] 2.2 [P2] [req: semantic-review-reference-doc] Add a link to the new reference from `docs/semantic-review.md`'s `## See also` list, wording it so the reader knows it carries the fields and values. The file sits at 97 lines against a 100-line cap for a concept doc, so the addition must cost at most two lines; report the file's line count before and after.
- [x] 3.1 [P3] [req: *] Run `python3 plugins/s/skills/document/scripts/docs_lint.py docs/semantic-review-reference.md docs/semantic-review.md` and fix every error by rewriting the prose — never by changing a doc-type marker to buy a larger cap, and never by padding a sentence across lines to dodge a word cap. Re-run until it exits `0`, and report the final result plus any warnings you chose to leave with the reason.
- [x] 3.2 [P3] [req: *] Verify the reference against each scenario in the delta, quoting the line that satisfies it: the cap and marker; all ten category values; the verdict rule and the suggestion conditions; both `lint` members with defaults; all four dispositions with only `replied` suppressing; the null-hash explanation; and the guide's link. Report any scenario the doc does not satisfy rather than editing the delta to match the doc.
- [x] 3.3 [P3] [req: *] Confirm the change touches only `docs/semantic-review-reference.md` and `docs/semantic-review.md` — `git status --porcelain` names those two plus the change's own `.shipd/` artifacts. Confirm no file under `plugins/` was modified, since every value was read rather than changed.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 87 | 18.5k |
| (no tool) | 0 | 3.6k |
| Agent | 4 | 3.5k |
| Read | 15 | 2.2k |
| Edit | 5 | 1.8k |
| Write | 1 | 1.8k |
| **Total** | 112 | 31.3k |
