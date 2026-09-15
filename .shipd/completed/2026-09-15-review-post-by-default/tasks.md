## 1. Pin the new default in tests

- [x] 1.1 [req: review-skill-references] In
      `plugins/s/skills/review/tests/test_skill_references.py`, add a test
      asserting that the `## References` table row for `posting.md` in
      `plugins/s/skills/review/SKILL.md` and the condition sentence under
      `plugins/s/skills/review/references/posting.md`'s level-1 title both contain the phrase "pull
      request" and neither contains "explicitly requested". Reuse the existing
      `TABLE_ROW_RE` and `_reference_condition_sentence` helpers. Run
      `python3 -m unittest discover -s plugins/s/skills/review/tests` and observe
      the new test fail.
- [x] 1.2 [req: skill-post-flow] In the same file, add a test asserting that
      `plugins/s/harness/bodies/review.md` and
      `plugins/s/harness/references/review.md` each contain neither "post only
      when the user explicitly asks" nor "Post only on an explicit request", and
      each state both that a named pull request is posted to by default and that
      dispositioning the findings is asked for rather than automatic. Run the
      suite and observe it fail.

## 2. Flip the posting default in the skill

- [x] 2.1 [req: skill-post-flow] In
      `plugins/s/skills/review/references/posting.md`, replace the opening load
      condition and the "Post only on an explicit request" rule with the new
      default: the file is read when a pull request is in scope for the review,
      and a review whose target is a named pull request posts its verdict
      without being asked. State that a bare `/s:review` naming no pull request
      posts nothing. Keep the level-1 title and keep the condition sentence
      directly under it.
- [x] 2.2 [req: skill-post-flow] In the same file, add the pull-request
      resolution ahead of the existing posting steps: accept a pull request URL,
      `#<number>`, a bare number, or a branch pointed at a pull request; resolve
      it with `gh pr view <target> --json number,headRefOid,baseRefName,url`; and
      review that head against that base with merge-base semantics.
- [x] 2.3 [req: skill-post-flow] In the same file, gate steps 6 and 7 — the
      disposition loop and `review_gate.py resolve` — on the invoker asking for
      the findings to be dispositioned, naming the two askers: a driving session
      declaring `disposition=<scope>`, and the user asking for the findings to be
      implemented or answered. Leave the per-scope text of both steps otherwise
      unchanged.
- [x] 2.4 [req: skill-post-flow] In the same file, state the default ending after
      step 5: implement no finding, author no reply, run neither `autoreply` nor
      `resolve`, and leave every posted thread open for the pull request's owner.
      Update step 8's report to require the unresolved count only where the
      disposition loop ran.
- [x] 2.5 [req: review-skill-references] In `plugins/s/skills/review/SKILL.md`,
      change the `## References` table row for `posting.md` so its `Load when`
      cell reads that a pull request is in scope for the review, keeping the
      note that the file also reads prior findings back before reporting.
- [x] 2.6 [req: review-skill-references] In the same file's "Determine what to
      review" section, add a third bullet for a named pull request that states
      the review posts to it by default and points at
      `${CLAUDE_PLUGIN_ROOT}/skills/review/references/posting.md` for the
      resolution, then compress the two existing bullets so the file stays under
      300 lines. Run `wc -l plugins/s/skills/review/SKILL.md` and confirm the
      count is below 300.

## 3. Carry the inversion to the reference-free surfaces

- [x] 3.1 [req: skill-post-flow] In `plugins/s/harness/bodies/review.md`, replace
      the `if:file-references` branch's "post only when the user explicitly asks"
      with the new default: a review naming a pull request posts to it, and
      implementing or resolving the findings happens only when asked. Leave the
      `else` branch's no-file-reference wording otherwise intact, adding the same
      default statement to it.
- [x] 3.2 [req: skill-post-flow] In `plugins/s/harness/references/review.md`,
      replace the "Post only on an explicit request" rule with the same default,
      gate its steps 5 and 6 on the invoker asking for a disposition, and state
      the default ending that leaves the threads open for the pull request's
      owner. Update the `## Disposition scope` table's introduction to say the
      scope narrows an opted-in disposition rather than the posting itself.

## 4. Update the concept guide

- [x] 4.1 [req: semantic-review-doc] In `docs/semantic-review.md`, rewrite the
      `## Where it runs` prose so it describes a local run that ends at the
      report and a run against a named pull request that posts by default, states
      that the posted findings stay open for that pull request's owner, and
      states that implementing and resolving them is an opt-in.
- [x] 4.2 [req: semantic-review-doc] In the same file, replace the single mermaid
      diagram's `posting requested` decision with a `PR target in scope`
      decision, and add the opt-in disposition branch so the loop back to the
      prior-dispositions node hangs off the opted-in path. Keep exactly one
      mermaid fence.
- [x] 4.3 [req: semantic-review-doc] Run `python3
      plugins/s/skills/document/scripts/docs_lint.py docs/semantic-review.md` and
      `wc -l docs/semantic-review.md`; confirm the lint exits 0 and the file is
      100 lines or fewer.

## 4b. Severity dot on posted findings

- [x] 4b.1 [req: gate-poster] In
      `plugins/s/skills/review/tests/test_review_gate.py`, extend the inline-body
      round-trip test so it asserts each rendered marker carries the matching
      `_SEV_DOT` entry directly before the severity word, and add a test that
      `parse_severity` still returns the severity from a dotless marker body
      (`"**high — something**"`). Add a test asserting the summary comment's
      folded-findings bullet for a medium finding carries the 🟠 dot. Run
      `python3 -m unittest discover -s plugins/s/skills/review/tests` and observe
      the new assertions fail.
- [x] 4b.2 [req: gate-poster] In
      `plugins/s/skills/review/scripts/review_gate.py`, replace the literal in
      `_sev_marker` with a single module-level format string carrying a dot
      placeholder and a severity placeholder; render `_sev_marker(severity)` from
      it using `_SEV_DOT`, and derive `_SEV_MARKER_RE` from that same format via
      the existing sentinel technique, making the dot group optional and
      non-capturing so the severity stays capture group 1 and a dotless body
      still parses. Do not hand-write the regex.
- [x] 4b.3 [req: gate-poster] In the same file's `render_summary`, prefix each
      "Additional findings" bullet's severity with its `_SEV_DOT` entry, leaving
      the location and the finding text unchanged.
- [x] 4b.4 [req: review-skill] In
      `plugins/s/integrations/copilot/copilot-review-gate.yml`, add the same
      severity-to-dot map to the posting step's inline Python and prefix the
      severity in both `inline_body` and the folded-finding line with the
      matching dot, matching `review_gate.py`'s rendering exactly.
- [x] 4b.5 [req: review-skill] In `plugins/s/skills/review/SKILL.md`'s
      Guardrails section, change the emoji rule from three sanctioned sites to
      four, naming the severity dot that prefixes a severity in an anchored
      inline comment and in a folded-findings bullet. Keep the file under 300
      lines; run `wc -l` to confirm.
- [x] 4b.6 [req: review-skill] In `plugins/s/integrations/copilot/SKILL.md`,
      update the emoji statement so the severity dot is also sanctioned wherever
      a posted finding names its own severity, leaving the `--json`/findings-file
      no-emoji rule intact.
- [x] 4b.7 [req: gate-poster, review-skill] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and confirm every test passes, including
      the pre-existing `parse_severity` round-trip and autoreply severity-
      selection tests.

## 5. Bump and verify

- [x] 5.0 [req: *] Bump `"version"` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.221` to the next
      patch version, since this change edits files under `plugins/s/` and
      the cache snapshot is keyed by version (AGENTS.md).

- [x] 5.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and confirm every test passes, including
      the two added in section 1 and the 300-line ceiling test.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 178 | 68.2k |
| Edit | 39 | 38.6k |
| Read | 29 | 12.7k |
| (no tool) | 0 | 7.9k |
| Agent | 2 | 1.2k |
| SendMessage | 1 | 431 |
| ToolSearch | 1 | 321 |
| **Total** | 250 | 129.3k |
