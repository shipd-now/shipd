## 1. Gate

- [x] 1.1 [req: declared-new-paths, non-path-token-skip, task-path-remedy] In `plugins/s/skills/build/tests/test_spec_gate.py`, add a `DeclaredNewPathTest(SpecGateTestBase)` class with one test per scenario of `declared-new-paths`. Extend `TaskFileReferenceCheckTest` with one test for each scenario of `non-path-token-skip` and the root scenario of `task-path-remedy`, and assert the remedy text in `test_deep_dangling_path_is_still_a_finding`. Use the paths and wording the scenarios give, `make_clean_change` and `write_tasks`, and create each directory a scenario says exists. For the outside-repository scenario, assert through `self.cli` on a path under a uniquely named missing directory. Run the file and observe the new tests for the changed behaviour fail.
- [x] 1.2 [req: declared-new-paths] In `plugins/s/skills/build/scripts/spec_gate.py`, add `declared_paths(text)`, returning the set of declared paths with one leading `./` stripped, exactly as the Declaration decision in `plan.md` defines.
- [x] 1.3 [req: declared-new-paths, non-path-token-skip, task-path-remedy] In `_check_task_paths` of the same file, pass a declared token, use existing-or-implied directories for the parent and grandparent tests, then apply the skip rule, then append the remedy to the finding, all as `plan.md` decides. Keep the existence and artefact checks first and keep the empty-string guards that exclude the root. Update the function docstring and check 3 in the module docstring.
- [x] 1.4 [req: declared-new-paths, non-path-token-skip, task-path-remedy] From `plugins/s/skills/build`, run `python3 -B -m unittest tests.test_spec_gate 2>&1` and grep the output for `^OK`.

## 2. Guidance

- [x] 2.1 [req: task-path-citation, enrichment-gap-diagnosis] In `plugins/s/skills/build/tests/test_external_loaders.py`, add a test that reads the Tasks part of `plugins/s/skills/plan/references/authoring.md` with whitespace collapsed and asserts it contains "full path from the repository root", "directly before" and "Never remove the backticks". Add a second test that asserts "directly before", "Never remove the backticks" and "placeholder directories" in both `plugins/s/skills/plan/references/enrichment.md` and `plugins/s/harness/references/plan.md`. Run it and observe both fail.
- [x] 2.2 [req: task-path-citation] In `plugins/s/skills/plan/references/authoring.md`, `## Tasks`, add after the bullet starting "Name the concrete file": "Cite each repository path in backticks, as the full path from the repository root. Write the word Create or Add directly before a path the task creates, with nothing between them. Never remove the backticks from a repository path to pass the gate, because later drift and overlap checks read them."
- [x] 2.3 [req: enrichment-gap-diagnosis] In the "Dangling task file references" bullet of `plugins/s/skills/plan/references/enrichment.md` and the "Resolve everything" bullet of `plugins/s/harness/references/plan.md`, add after the correction sentence: "When the task creates the path, write Create directly before it. Never remove the backticks from a repository path, and never create placeholder directories, to clear the finding."
- [x] 2.4 [req: task-path-citation, enrichment-gap-diagnosis] From `plugins/s/skills/build`, run `python3 -B -m unittest tests.test_external_loaders 2>&1` and grep the output for `^OK`.

## 3. Version and verification

- [x] 3.1 [req: *] Run `git fetch origin main`, read `version` from `plugins/s/.claude-plugin/plugin.json` on the fetched main, and set the local file's `version` one patch above it.
- [x] 3.2 [req: *] From `plugins/s/skills/build`, run `python3 -B -m unittest discover -s tests 2>&1` and grep the output for `^OK` or `^FAILED`. From the repository root, run `python3 -B -m unittest discover -s tools/tests 2>&1` and grep it the same way. Both report OK.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 47 | 20.6k |
| SubagentHandback | 5 | 4.0k |
| Monitor | 7 | 1.9k |
| Agent | 4 | 1.4k |
| (no tool) | 0 | 933 |
| SendMessage | 2 | 846 |
| ToolSearch | 1 | 707 |
| TaskStop | 1 | 370 |
| Skill | 1 | 243 |
| **Total** | 68 | 31.0k |
