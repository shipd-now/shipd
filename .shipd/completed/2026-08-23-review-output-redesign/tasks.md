## 1. Carry suggestions in the poster

- [x] 1.1 [req: gate-poster] Add cases to
      `plugins/s/skills/review/tests/test_review_gate.py` asserting: a finding
      declaring a confident fix with a contiguous whole-line replacement that
      anchors renders an inline body containing a ```suggestion fenced block
      carrying those lines; a multi-line replacement carries every line; a
      confident finding whose location does not anchor is folded into the
      summary with no suggestion; a replacement covering part of a line renders
      no suggestion; and a suggestion-carrying body still opens with the marker
      `parse_severity` reads. Run the suite and observe them fail.
- [x] 1.2 [req: gate-poster] In
      `plugins/s/skills/review/scripts/review_gate.py`, extend `_inline_body`
      to append a ```suggestion fenced block when the finding declares its fix
      confident and carries a whole-line replacement, leaving the leading
      severity marker and the existing what/why/fix prose unchanged. Split the
      docstring's coupled sentence so it forbids emoji only.
- [x] 1.3 [req: gate-poster] In the same file, gate suggestion emission on the
      finding's location anchoring to a RIGHT-side commentable line — reusing
      the existing anchoring decision rather than recomputing it — so an
      unanchorable finding folds into the summary as prose.
- [x] 1.4 [req: gate-poster] In the same file, assert the review POST continues
      to submit the event `COMMENT`, and add a test pinning it so the event
      cannot drift silently.
- [x] 1.5 [req: gate-poster] In `plugins/s/skills/review/SKILL.md`'s Machine
      output mode schema, document the optional per-finding `suggestion`
      object (`confident`, `start_line`, `end_line`, `lines`) and the rule
      that the poster emits a committable block only for a confident,
      contiguous whole-line replacement that anchors — leaving the emoji- and
      prose-free rules of `--json` unchanged.

## 2. Treat an applied suggestion as implemented

- [x] 2.1 [req: skill-post-flow] In
      `plugins/s/skills/review/SKILL.md`, update the disposition loop's `all`
      scope so an applied committable suggestion counts as the implement
      branch and needs no separate reply, while a finding that is neither
      implemented nor applied still requires a reasoned reply before
      resolution.

## 3. Mandate the report shape and the findings file

- [x] 3.1 [req: skill-template] In
      `plugins/s/integrations/copilot/SKILL.md`, require the review body to
      open with a verdict header and a severity summary table before any
      per-finding detail, and to keep each finding's detail brief.
- [x] 3.2 [req: skill-template] In the same template, require the agent to
      write a machine-readable findings file beside the body, each entry
      carrying severity, path, line range, and detail, and carrying a
      replacement only where the agent judges the fix confident and expressible
      as one or more contiguous whole lines. Name the file path the gate
      workflow reads it from.
- [x] 3.3 [req: skill-template] Add a case to
      `plugins/s/skills/build/tests/test_copilot_verb.py` asserting the
      template names the verdict header, the severity table, and the findings
      file with its replacement rule.

## 4. Post a real review from the gate

- [x] 4.1 [req: gate-workflow-template] Add cases to
      `plugins/s/skills/build/tests/test_copilot_verb.py` asserting the
      gate template posts through the pull-request reviews API with the event
      `COMMENT` on its own reviewer's path, that it verifies each finding's
      path and line range against the diff it computed before anchoring, that
      an unverifiable finding is folded into the body as prose, and that the
      reviewer step and the posting step bind different credentials. Run the
      suite and observe them fail.
- [x] 4.2 [req: gate-workflow-template] In
      `plugins/s/integrations/copilot/copilot-review-gate.yml`, replace the
      `gh pr comment` publication on the gate's own reviewer path with a
      pull-request review POST carrying the body and the anchored inline
      comments, submitting the event `COMMENT`. Leave the poll-fallback path,
      which reads GitHub's own review, unchanged.
- [x] 4.3 [req: gate-workflow-template] In the same workflow, read the findings
      file the reviewer wrote, verify each finding's path and line range
      against the diff the posting step computes itself, drop unverifiable
      findings into the body as prose, and attach a ```suggestion block to an
      anchored comment whose finding carries a replacement.
- [x] 4.4 [req: gate-workflow-template] Confirm the reviewer step still binds
      only the reviewer token and the posting step only the workflow token, so
      the findings file remains the only channel between them.

## 5. Verification

- [x] 5.0 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` by one patch level, so the cached
      plugin snapshot refreshes with this change.
- [x] 5.1 [req: *] Run the engine test suite under
      `plugins/s/skills/build/tests/` and confirm every test passes.
- [x] 5.2 [req: *] Run `python3 -c "import ast,sys; ast.parse(open('plugins/s/skills/review/scripts/review_gate.py').read())"`
      and confirm the poster still parses, then confirm it imports without any
      third-party module so the constitution's stdlib-only rule holds.
- [x] 5.3 [req: *] Confirm `plugins/s/integrations/copilot/copilot-review-gate.yml`
      is valid YAML by parsing it with the standard library.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 142 | 66.1k |
| Edit | 53 | 39.9k |
| (no tool) | 0 | 8.6k |
| Read | 28 | 4.2k |
| Write | 2 | 2.7k |
| Agent | 2 | 2.2k |
| SendMessage | 1 | 1.6k |
| ToolSearch | 1 | 115 |
| **Total** | 229 | 125.4k |
