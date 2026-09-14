# review-finding-category

- [x] 1.1 [P1] [req: review-taxonomy-parity] Extend `plugins/s/skills/review/tests/test_skill_references.py` with the assertions this change must satisfy, and confirm they FAIL before any other task is claimed. Add module-level constants for the two taxonomy sites (`plugins/s/skills/review/references/json-output.md` and `plugins/s/harness/references/review.md`, the latter reached from the tests directory via the plugin root) and a helper that extracts a taxonomy line's field name and its quoted values. Assert: both sites name the field `category`; neither names it `cohort` or `kind`; the two value sets are exactly equal, failing with the symmetric difference named; and the set contains all ten of `bug`, `contract`, `edge-case`, `untouched-caller`, `spec-coverage`, `test-coverage`, `security`, `performance`, `stability`, `data-integrity`. Update the existing assertion at line 322 that reads `'"cohort":'` so it reads the renamed field. Do not weaken any existing assertion.
- [x] 2.1 [P2] [req: review-skill] Edit `plugins/s/skills/review/references/json-output.md` line 17: rename the `"cohort"` key to `"category"`, leaving its ten values and every other line unchanged.
- [x] 2.2 [P2] [req: review-taxonomy-parity] Edit `plugins/s/harness/references/review.md` line 24: rename the `"cohort"` key to `"category"` and extend its values from the current five to the full ten, adding `test-coverage`, `security`, `performance`, `stability` and `data-integrity`. Match the plugin reference's value order exactly so the two lines read alike. Change nothing else in the file.
- [x] 2.3 [P2] [req: review-skill] Edit `plugins/s/skills/review/SKILL.md` line 180, changing the prose "`test-coverage` cohort" to "`test-coverage` category". This is the only taxonomy mention in that file — the other twelve `cohort` mentions are architectural and must stay exactly as they are, including `### 6. Report by cohort` and the `## References` table.
- [x] 3.1 [P3] [req: *] Bump `"version"` in `plugins/s/.claude-plugin/plugin.json` to `0.6.217`, per the cache-snapshot rule in AGENTS.md.
- [x] 3.2 [P3] [req: *] Verify the rename missed nothing and took nothing extra. Run `grep -rn '"cohort"' plugins/s/` and confirm it returns no taxonomy site (a hit inside `semdiff.py` or its tests is the architectural grouping and is expected). Then run `grep -c cohort plugins/s/skills/review/SKILL.md` and confirm it reports 12, one fewer than before this change. Report both outputs.
- [x] 3.3 [P3] [req: *] Run `python3 -m unittest discover -s plugins/s/skills/review/tests -v` and confirm every test passes, task 1.1's new assertions included. Then run `python3 -m unittest discover -s plugins/s/skills/build/tests -v` and confirm no regression — `test_harness_bodies.py` reads the harness reference that task 2.2 edits.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 106 | 22.1k |
| Edit | 7 | 9.8k |
| (no tool) | 0 | 5.3k |
| Agent | 4 | 1.9k |
| Read | 13 | 1.7k |
| Monitor | 3 | 843 |
| SendMessage | 1 | 638 |
| ToolSearch | 2 | 183 |
| **Total** | 136 | 42.5k |
