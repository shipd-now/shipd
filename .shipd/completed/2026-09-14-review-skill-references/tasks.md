# review-skill-references

- [x] 1.1 [P1] [req: review-skill-references] Add `plugins/s/skills/review/tests/test_skill_references.py`, a stdlib-only `unittest` module asserting the whole structure: `SKILL.md` is under 300 lines; it carries no `## Machine output mode`, `## Posting to a PR`, or `## Spec-aware review` heading; it still carries the workflow steps, the `high`/`medium`/`low` severity rubric and the `command -v difft` probe; every `references/*.md` file is named by path in `SKILL.md`; every reference path named in `SKILL.md` exists; each reference file opens with a level-1 title and states its load condition; and neither `plugins/s/integrations/copilot/SKILL.md` nor `plugins/s/harness/bodies/review.md` names a path under `skills/review/references/`. Run it and confirm it FAILS before any other task is claimed — the split does not exist yet.
- [x] 2.1 [P2] [req: review-skill-references] Create `plugins/s/skills/review/references/spec-aware.md`. Move `SKILL.md`'s `## Spec-aware review (when a shipd change is in scope)` section (lines 152–172 of the pre-change file) into it verbatim, promoting the heading to a level-1 title `# Spec-aware review`. Directly under the title, add one sentence naming the load condition: the skill reads this file when the user names a planned change, or exactly one change exists under `planned/`. Change no other word of the moved text.
- [x] 2.2 [P2] [req: review-skill-references] Create `plugins/s/skills/review/references/json-output.md`. Move `SKILL.md`'s `## Machine output mode (--json)` section including its `### The optional suggestion object` subsection (lines 203–272 of the pre-change file) into it verbatim, promoting the section heading to a level-1 title `# Machine output mode` and demoting `### The optional suggestion object` to level 2. Directly under the title, add one sentence naming the load condition: the skill reads this file when the user passes `--json`, or when it is producing the JSON object the poster consumes. Change no other word of the moved text.
- [x] 2.3 [P2] [req: review-skill-references] Create `plugins/s/skills/review/references/posting.md`. Move `SKILL.md`'s `## Posting to a PR (the gate)` section including its `### Review stage options` subsection (lines 273–411 of the pre-change file) into it verbatim, promoting the section heading to a level-1 title `# Posting a review to a PR` and demoting `### Review stage options` to level 2. Directly under the title, add one sentence naming the load condition: the skill reads this file only when posting was explicitly requested, by the user or by a driving session. Change no other word of the moved text.
- [x] 3.1 [P3] [req: review-skill-references] Edit `plugins/s/skills/review/SKILL.md`: delete the three moved sections, leaving `## Degradation`, `## Documentation standard`, `## Guardrails` and `## Question rejection recovery` in place and unedited. Insert a `## References` section directly after the `semdiff` invocation block and above `## Determine what to review`, holding one introductory sentence stating that each file is read only when its condition fires, then a two-column markdown table with headers `Reference` and `Load when`, one row per reference naming the file as `${CLAUDE_PLUGIN_ROOT}/skills/review/references/<name>.md`. Fix every cross-reference the deletions broke — step 7 points at the `test-coverage` cohort "see the Machine output mode shape below", the Presentation section points at the `--json` verdict, and the Guardrails point at `--json` output; each must now name the owning reference file instead of a section below.
- [x] 3.2 [P3] [req: *] Bump `"version"` in `plugins/s/.claude-plugin/plugin.json` from `0.6.214` to `0.6.215`, per the cache-snapshot rule in AGENTS.md.
- [x] 4.1 [P4] [req: *] Run `python3 -m unittest discover -s plugins/s/skills/review/tests -v` from the repo root and confirm every test passes, task 1.1's new module included. Then run `python3 -m unittest discover -s plugins/s/skills/build/tests -v` and confirm no regression, since `test_harness_bodies.py` and `test_copilot_verb.py` both read skill bodies.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 144 | 50.5k |
| Write | 7 | 13.4k |
| Edit | 8 | 8.7k |
| (no tool) | 0 | 6.9k |
| Read | 26 | 3.7k |
| Agent | 4 | 2.5k |
| AskUserQuestion | 2 | 2.4k |
| ToolSearch | 3 | 2.1k |
| WebFetch | 1 | 142 |
| **Total** | 195 | 90.3k |
