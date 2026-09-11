# review-depth
Status: verified

## Idea

Deepen `/s:review` so it reads new code, chases changed constants, checks its own
test coverage, and anchors every finding on the right line.

### Motivation

`semdiff` reports an added file as a filename and a line count, so brand-new code
ships unreviewed, and its difft engine emits 0-based hunk lines while its text
engine emits 1-based, so the merge gate anchors inline comments one line high.

### Details

- Inline an added file's line-numbered body in `semdiff diff` output, capped.
- Normalize difft hunk lines to 1-based so both engines agree with `grep -n`.
- Add three judgement passes to the skill: changed constants and uneven sibling
  sites, new code judged on its own terms, and a per-finding test-coverage check.
- Add the `test-coverage` cohort to the `--json` finding shape.
- Bind the skill's rendered report and posted comment to the shipd documentation
  standard.
- Carry the same passes into the harness body so the two surfaces do not drift.

Affected capabilities: `semantic-review` (modified). Impact:
`plugins/s/skills/review/scripts/semdiff.py`,
`plugins/s/skills/review/SKILL.md`, `plugins/s/harness/bodies/review.md`,
`plugins/s/skills/review/tests/test_semdiff_diff.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No change to `review_gate.py`. It consumes line numbers; it does not produce
  them, and its own tests use synthetic JSON.
- No rewrite of `SKILL.md` prose to pass `docs_lint.py`. The binding governs the
  review's output, not the skill file.
- No new `semdiff` subcommand, and no diagram policy change.

## Implementation

- **Normalize at the source.** `summarize_chunks` adds 1 to difft's
  `line_number` so every emitted hunk is 1-based, matching the text engine and
  `git`. Rejected: correcting downstream in the skill — the JSON is the contract
  the poster anchors on, so a consumer-side fix leaves the artifact wrong.
- **`_touches_declaration_difft` shifts with it.** It indexes `lines[ln]` on a
  0-based hunk line (`semdiff.py:340`); once hunks are 1-based it must index
  `lines[ln - 1]`, or the signature-change estimate slides by one line. This is
  the one coupled site, and it has no test today.
- **Inline added-file bodies in both engines.** A shared `_inline_content` helper
  returns a line-numbered body plus a `content_truncated` flag, capped at 600
  lines and 60 KB — the reference implementation's caps, which keep a vendored
  blob from swamping the review. It attaches at `semdiff.py:374` (difft) and
  `semdiff.py:448` (text), so a degraded review inlines new files too.
- **Line numbers now mean one thing.** Inlined `content` is 1-based and so is
  every hunk, so the JSON carries a single numbering convention.
- **Bind the output, not the skill file.** `SKILL.md` gains a short section
  pointing at `skills/document/references/standard.md` by path, governing the
  rendered report and the posted summary comment, and fixing `finding` as the
  glossary term. Rejected: restating the rules — the standard says one file holds
  them, and a copy drifts.
- **Parity by contract.** The harness body carries the same three passes in its
  terser register, and the delta requirement names both surfaces so a future
  edit to one without the other fails review.

Risk: the off-by-one fix moves every difft-engine finding one line. That is the
correction, not a regression, and the new tests pin it against `grep -n` truth.
