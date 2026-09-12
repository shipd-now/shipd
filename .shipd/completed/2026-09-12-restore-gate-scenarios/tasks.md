# tasks

- [x] 1.1 [req: gate-poster] Confirm each of the seven restored `gate-poster` scenarios describes what `plugins/s/skills/review/scripts/review_gate.py` actually does, reading `status_state` (the three disposition scopes), `_upsert_summary` (create, edit-in-place, legacy-marker lookup), `_split_findings` and `_post_review` (anchored versus folded findings), and `render_summary` (the `Disposition:` and `Model:` provenance lines). Report any scenario whose wording does not match the code rather than editing the code to match
- [x] 1.2 [req: gate-poster] Map each of the seven restored scenarios to the existing test in `plugins/s/skills/review/tests/test_review_gate.py` that already exercises it, and report any that has no covering test. Add a test only where one is genuinely missing; do not duplicate coverage that already exists
- [x] 1.3 [req: skill-post-flow] Confirm the three restored `skill-post-flow` scenarios match `plugins/s/skills/review/SKILL.md`'s disposition loop for scopes `all`, `high-only` and `none`, and that the autoreply severity selection in `review_gate.py` agrees with them. These describe an agent flow, so they are specified but not unit-tested — report the match, add no test
- [x] 2.1 [req: *] Run `python3 -m unittest discover -s plugins/s/skills/review/tests -v` from the repo root and confirm the review suite passes. Then run the change lint and confirm the retention rule accepts the delta, which restates every scenario both requirements already carried
- [x] 2.2 [req: *] Decide whether `plugins/s/.claude-plugin/plugin.json` needs a version bump. AGENTS.md requires one for every change touching `plugins/s/`, but this change edits only delta specs under the content directory and no file under `plugins/s/` — so the rule may not apply. State your conclusion and bump only if it does apply.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 66 | 32.0k |
| Agent | 2 | 1.2k |
| (no tool) | 0 | 890 |
| **Total** | 68 | 34.1k |
