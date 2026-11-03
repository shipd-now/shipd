## 1. Engine guard and head disclosure

- [x] 1.1 [req: empty-head-refusal] In `plugins/s/skills/review/tests/test_semdiff_diff.py`, add tests to `DiffTestCase`: (a) with no extra setup — the fixture's `main` is an ancestor of `feature` — `diff feature main`, `files feature main`, and `lint feature main` each exit 1 with empty stdout and stderr containing `main`, `feature`, and `adds nothing over base`; (b) `diff main main --linear` exits 1 with stderr containing `adds nothing over base`; (c) after discarding the fixture's working-tree edits with `git checkout -- .` and `git clean -fdq` in the test repo, `diff main` exits 0 with `summary.files` 0. Run the file and observe (a) and (b) fail.
- [x] 1.2 [req: endpoint-disclosure] In `plugins/s/skills/review/tests/test_semdiff_diff.py`, extend `test_endpoints_disclosed_as_commit_ids` to assert `out["head_given"] == "feature"`, and `test_working_tree_mode_discloses_null_head_and_fork_point` to assert `out["head_given"]` is None. Run them and observe them fail.
- [x] 1.3 [req: endpoint-disclosure] In `resolve_endpoints` in `plugins/s/skills/review/scripts/semdiff.py`, add `"head_given": head` to the meta dict of all three modes (working-tree, linear, merge-base), beside `base_given`, and add `head_given` to the docstring's meta list.
- [x] 1.4 [req: empty-head-refusal] In `resolve_endpoints` in `plugins/s/skills/review/scripts/semdiff.py`: under `--linear`, before returning, call `die(...)` when `head_sha == base_sha`; in merge-base mode, after computing `mb`, call `die(...)` when `head_sha == mb`. The message is `f"head '{head}' ({head_sha[:7]}) adds nothing over base '{base_given}' ({base_sha[:7]}) — nothing to review; check the head ref."` with the default exit code 1. Add no check to working-tree mode. Confirm tasks 1.1 and 1.2 now pass.

## 2. Skill prose and payload docs

- [x] 2.1 [req: review-base-fetch] In `plugins/s/skills/review/SKILL.md`'s "Base freshness" block (around lines 47-63), add a paragraph before the `git fetch` command: where a head ref is given, first run `git rev-parse --verify <head>^{commit}` and pass the printed commit id as `<head>` to every `semdiff` call, keeping the name for `head_given`; only the head is frozen, so the base still resolves to its freshly fetched remote-tracking commit; the named-PR path already passes commit ids.
- [x] 2.2 [req: endpoint-disclosure] In `plugins/s/skills/review/SKILL.md`'s Presentation item 2 "Resolved endpoints" (around lines 222-226), add: where the head as given differs from `head_sha`, name it beside the commit id, e.g. `head FETCH_HEAD → 8d2e59e`.
- [x] 2.3 [req: empty-head-refusal] In `plugins/s/skills/review/SKILL.md`, directly after the Base freshness block's failed-fetch sentence, add: when `semdiff` exits 1 with "adds nothing over base", print `Nothing to review` and the endpoints line, emit no `## Findings` verdict, and post nothing to a pull request.
- [x] 2.4 [req: endpoint-disclosure] In `plugins/s/skills/review/references/json-output.md`, add `"head_given": "feature" | null,` to the `endpoints` example directly above `"head"`, and in the prose near line 63 state that `head_given` is the head ref the invoker named before the skill froze it, while every other field comes straight from `semdiff`'s meta.
- [x] 2.5 [req: endpoint-disclosure] In `plugins/s/harness/references/review.md`, make the identical two edits task 2.4 made: the `"head_given"` line in the `endpoints` example and the same prose sentence near line 66.
- [x] 2.6 [req: endpoint-disclosure, review-base-fetch, empty-head-refusal] In `plugins/s/skills/review/tests/test_skill_references.py`, add `"head_given"` to the endpoints `FIELDS` tuple (around line 1442), and add a test asserting `SKILL.md` contains `rev-parse --verify`, `head_given`, and `Nothing to review`. Run `python3 -m unittest discover -s plugins/s/skills/review/tests` and confirm it passes.

## 3. Version and verification

- [x] 3.1 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json` to the next patch above the version on the remote main branch at build time.
- [x] 3.2 [req: *] Run `python3 -m unittest discover -s plugins/s/skills/review/tests` and `python3 -m unittest discover -s plugins/s/skills/build/tests`, grep each run's output for `OK` or `FAILED`, and confirm both report `OK`. Confirm `plugins/s/harness/bodies/review.md` is unchanged against the remote main branch: `git diff --exit-code` on that file must exit 0.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 31 | 12.9k |
| SubagentHandback | 3 | 2.5k |
| bash | 1 | 1.7k |
| Agent | 2 | 1.1k |
| (no tool) | 0 | 550 |
| **Total** | 37 | 18.8k |
