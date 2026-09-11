## 1. Line numbering

- [x] 1.1 [req: structural-diff] In
      `plugins/s/skills/review/tests/test_semdiff_diff.py`, add a test that
      commits a ten-line file, edits only line 10, and asserts the after-side
      hunk reports `line` 10 — run it twice, once with `difft` on PATH and once
      with PATH restricted so the text engine runs. Run it and observe the
      difft case fail with 9.
- [x] 1.2 [req: structural-diff] In `summarize_chunks` in
      `plugins/s/skills/review/scripts/semdiff.py`, add 1 to difftastic's
      `line_number` when building each hunk, so emitted hunks are 1-based.
- [x] 1.3 [req: structural-diff] In `_touches_declaration_difft` in
      `plugins/s/skills/review/scripts/semdiff.py`, index the file body at
      `lines[ln - 1]` and bound the check at `1 <= ln <= len(lines)`, matching
      the now 1-based hunk lines. Confirm `test_semdiff_diff.py` passes.

## 2. Added-file content

- [x] 2.1 [req: structural-diff] In
      `plugins/s/skills/review/tests/test_semdiff_diff.py`, add tests that a
      newly added three-line file carries `content` with lines prefixed `1`,
      `2`, `3` and `content_truncated` false, and that a newly added file of
      more than 600 lines carries 600 content lines and `content_truncated`
      true. Cover both the difft and text engines. Run them and observe them
      fail — `content` does not exist yet.
- [x] 2.2 [req: structural-diff] In
      `plugins/s/skills/review/scripts/semdiff.py`, add a module-level
      `_inline_content(text)` helper returning a line-numbered body and a
      truncation flag, capped by new `ADDED_CONTENT_MAX_LINES = 600` and
      `ADDED_CONTENT_MAX_BYTES = 60_000` constants.
- [x] 2.3 [req: structural-diff] In `_difft_entry` in
      `plugins/s/skills/review/scripts/semdiff.py`, set `content` and
      `content_truncated` from `_inline_content` on the `added` branch that
      currently sets only `lines`.
- [x] 2.4 [req: structural-diff] In `_text_entry` in
      `plugins/s/skills/review/scripts/semdiff.py`, set `content` and
      `content_truncated` the same way on its `added` branch. Confirm
      `test_semdiff_diff.py` passes.

## 3. Skill passes

- [x] 3.1 [req: review-skill] In `plugins/s/skills/review/SKILL.md`, extend
      step 3 with the changed-constant rule (a changed limit, bound, timeout,
      retry count, buffer size or threshold is a contract change, chased
      through `context`) and the uneven-sibling-site rule (compare parallel
      implementations against each other, naming the asymmetry).
- [x] 3.2 [req: review-skill] In `plugins/s/skills/review/SKILL.md`, add a new
      step between the current steps 4 and 5 that judges newly added code on
      its own terms: wrong quantity measured, escape hatch lapsing the
      guarantee, termination on hostile input, boundary agreement, and doc
      comment versus code. Renumber the following step.
- [x] 3.3 [req: review-skill] In `plugins/s/skills/review/SKILL.md`, add a
      per-finding test-coverage step running at every severity, and add
      `test-coverage` to the `cohort` enum in the Machine output mode JSON
      shape.
- [x] 3.4 [req: review-skill] In `plugins/s/skills/review/SKILL.md`, replace
      the guardrail sentence permitting a reviewer to skip a new file with the
      rule that an added file's inlined `content` is reviewed like a hunk, and
      that a true `content_truncated` means reading the remainder.

## 4. Standard binding and parity

- [x] 4.1 [req: review-skill] In `plugins/s/skills/review/SKILL.md`, add a
      short section binding the rendered report and the posted summary comment
      to `${CLAUDE_PLUGIN_ROOT}/skills/document/references/standard.md`,
      naming the file by path, restating no rule from it, and fixing "finding"
      as the term for one reported defect.
- [x] 4.2 [req: review-skill] In `plugins/s/harness/bodies/review.md`, extend
      steps 4 and 5 with the changed-constant and sibling-site rules, add the
      new-code pass and the per-finding test-coverage check, and keep the
      rendered body under the 120-line cap.

## 5. Ship

- [x] 5.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to the next patch, as AGENTS.md
      requires for any change touching `plugins/s/`.
- [x] 5.2 [req: *] Run
      `python3 -m unittest discover -s plugins/s/skills/review/tests` and
      confirm every test passes, including the new ones.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 87 | 27.9k |
| Edit | 15 | 11.9k |
| Read | 20 | 4.1k |
| (no tool) | 0 | 3.6k |
| Agent | 2 | 2.3k |
| **Total** | 124 | 49.8k |
