## 1. Protect verb 404 tolerance

- [x] 1.1 [req: required-check-protect] In
      `plugins/s/skills/review/tests/test_review_gate.py`, add failing tests
      for `protect` on an unprotected branch, driven through the injected
      `gh` runner per the file's existing pattern: a protection GET returning
      the not-protected 404 → a PUT creating
      `required_status_checks: {strict: false, contexts:
      ["semantic-review"]}` with `required_conversation_resolution` true and
      the other PUT keys null; a GET failing with any other error (e.g. 403)
      → the verb fails naming the read error with no write; the existing
      protected-branch behavior unchanged. Run them and observe them fail.
- [x] 1.2 [req: required-check-protect] Implement the tolerance in
      `plugins/s/skills/review/scripts/review_gate.py`'s `protect`:
      distinguish the not-protected 404 from other GET failures (the error
      text carries `HTTP 404` / "Branch not protected"), treat it as
      `current = {}`, and pass `strict: false` for that creation case while
      an existing protection keeps its preserved `strict`.
- [x] 1.3 [req: required-check-protect] Confirm the new tests pass and run
      the review suite (`python3 -m unittest discover -s
      plugins/s/skills/review/tests -q`) plus the engine suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests -q`).

## 2. The /s:copilot skill and its body template

- [x] 2.1 [req: copilot-skill-flow] Author
      `plugins/s/skills/copilot/SKILL.md` implementing the flow requirement:
      frontmatter (`name: copilot`, description carrying the `/s:copilot`
      trigger and phrases like "set up copilot review", "install the review
      gate"); version announcement; preflight with hand-offs; `shipd copilot
      add` via the doctor-style binary resolution; commit/push step with the
      `shipd-copilot-install` branch fallback; the single batched consent
      round (protect via
      `python3 "${CLAUDE_PLUGIN_ROOT}/skills/review/scripts/review_gate.py"
      protect`, auto-merge PATCH omitted under resolved `pr-mode: draft`,
      optional `SHIPD_GATE_FAIL_OPEN=false` with its pending trade-off
      stated) honoring dialog-prose separation; the minimal-PAT relay and
      `! gh secret set COPILOT_GITHUB_TOKEN` hand-off with the
      advisory-until-set statement; the closing `shipd doctor` verification
      reporting the `protection`/`automerge`/`copilot-secret` lines; and the
      question-rejection recovery rule.
- [x] 2.2 [req: copilot-skill-registration] Add
      `plugins/s/harness/bodies/copilot.md`: a distilled router opening with
      a `<!-- description: … -->` marker (one line, matching the skill's
      purpose), `<!-- include:preamble -->`, and an ungated body pointing at
      the skill flow — no `if:` gates, so no fallback reference file. Run the
      engine suite and confirm the bodies/skills id-set equality test passes.

## 3. Registration, docs, version

- [x] 3.1 [req: copilot-skill-registration] Add the `/s:copilot` row to
      `README.md`'s skills table and extend `AGENTS.md`'s skill enumeration
      sentence with `/s:copilot` (set up the copilot review gate).
- [x] 3.2 [req: *] In `docs/copilot-review.md`, name `/s:copilot` as the
      guided setup path near the top of the setup section (section 1), with
      the manual steps remaining as the reference.
- [x] 3.3 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` to the next
      patch version above the version current at ship time (0.6.144 if main
      is still at 0.6.143).

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 151 | 57.7k |
| (no tool) | 0 | 19.1k |
| Edit | 23 | 12.1k |
| Write | 3 | 10.0k |
| Agent | 7 | 6.3k |
| Read | 26 | 3.4k |
| ToolSearch | 1 | 449 |
| WebSearch | 2 | 213 |
| **Total** | 213 | 109.3k |
