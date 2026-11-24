## 1. The config key

- [x] 1.1 [req: distinct-reviewer-key] In `plugins/s/skills/build/tests/test_config_registry.py`, add failing tests: `resolve_distinct_reviewer` returns `False` with no declaration, returns `True` from a workspace root's config for a member beneath it, and raises `ConfigError` naming `distinct_reviewer`, the value and the file for `"yes"`; `config-set distinct_reviewer true` exits 0 and writes the key; `config-set distinct_reviewer maybe` exits 1 with the hint `true or false`. Run the file and see it fail.
- [x] 1.2 [req: distinct-reviewer-key] In `plugins/s/skills/build/scripts/spec_common.py`, add `distinct_reviewer` to `RECOGNIZED_CONFIG_KEYS` and add `distinct_reviewer_from_config` and `resolve_distinct_reviewer` per plan.md. In `plugins/s/skills/build/scripts/config_registry.py`, add the registry row per plan.md. Run 1.1's tests until they pass.
- [x] 1.3 [req: distinct-reviewer-key] In `plugins/s/skills/build/references/shipd.config.example.json`, add a `// distinct_reviewer` entry after `// room`, stating the default `false` and what `true` makes the room verbs do. Run `plugins/s/skills/build/tests/test_config_sample.py` and fix the sample until it passes.

## 2. The room verbs

- [x] 2.1 [req: room-whoami-verb] In `plugins/s/skills/room/tests/test_room.py`, add failing tests for `whoami` on the author's account: with no `distinct_reviewer` it exits 0 with `is_author` true and `may_approve` false; with `distinct_reviewer` true it prints one `Error:` line naming `distinct_reviewer` and exits 1. Change the existing author-refused and bot-refused `whoami` tests to set `distinct_reviewer` true. Run the file and see the new tests fail.
- [x] 2.2 [req: room-whoami-verb] In `plugins/s/skills/room/scripts/room.py`, add `_distinct_reviewer(root)` and change `cmd_whoami` per plan.md, until 2.1 passes.
- [x] 2.3 [req: room-run-start] In `plugins/s/skills/room/tests/test_room_run.py`, add a failing test: `run 7 --role reviewer` on the author's account with no `distinct_reviewer` writes the comment-review warning to stderr and posts the card. Change the two existing refused-at-start tests to set `distinct_reviewer` true. Run the file and see the new test fail.
- [x] 2.4 [req: room-run-start] In `plugins/s/skills/room/scripts/room_run.py`, change `_check_identity` and its caller per plan.md, until 2.3 passes.
- [x] 2.5 [req: room-run-repo-poll] In `plugins/s/skills/room/tests/test_room_run_repo.py`, add a failing test: with no `distinct_reviewer`, a PR authored by the acting login that holds a task gets one runner call. Change the existing skipped-PR test to set `distinct_reviewer` true. Run the file and see the new test fail.
- [x] 2.6 [req: room-run-repo-poll] In `plugins/s/skills/room/scripts/room_run_repo.py`, read the flag once at start and gate the same-account skip on it per plan.md, until 2.5 passes.

## 3. Skill copies and docs

- [x] 3.1 [req: room-skill-identity-check] In `plugins/s/skills/room/tests/test_room_skill.py`, add a failing test that `plugins/s/skills/room/SKILL.md`, `plugins/s/harness/bodies/room.md` and `plugins/s/harness/references/room.md` each name `may_approve` and say such a review posts as a comment. Then edit the three files per plan.md, changing no heading, until it passes. Run `plugins/s/skills/build/tests/test_harness_bodies.py` and `plugins/s/skills/build/tests/test_external_loaders.py` and keep both green.
- [x] 3.2 [req: agent-identity-docs-version] Revise `docs/agent-identity.md` to the modified requirement, against `plugins/s/skills/document/references/standard.md`: a second account is optional, `## When to use it` names the two cases and the `distinct_reviewer` behaviour, and `## Reference` adds `customise.md`. Run `plugins/s/skills/document/scripts/docs_lint.py docs/agent-identity.md` until it exits 0.
- [x] 3.3 [req: agent-identity-docs-version] In `docs/room-run.md` (lines 31-32 and 145) and `docs/multi-agent-pr.md` (line 89), replace the wording that a reviewer needs its own account with wording that a second account is optional, keeping each link to `agent-identity.md`. In `docs/pr.md`, add the single-account merge values per plan.md and reword line 120 the same way. Run `docs_lint.py` on the three pages until each exits 0.
- [x] 3.4 [req: distinct-reviewer-key] In `docs/customise.md`, add a `distinct_reviewer` row to the key table, in the table's key order. Run `docs_lint.py docs/customise.md` until it exits 0.
- [x] 3.5 [req: agent-identity-docs-version] In `plugins/s/.claude-plugin/plugin.json`, set the version one patch above the version the main branch carries at build time.

## 4. Verify

- [x] 4.1 [req: *] Run `python3 -m unittest discover -s plugins/s/skills/build/tests`, `python3 -m unittest discover -s plugins/s/skills/room/tests`, and `docs_lint.py` on the five docs pages. Then, in a scratch repository, run `spec_status.py config-set distinct_reviewer true` and confirm `shipd room whoami` paths through the fake-`gh` tests cover both settings.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 97 | 45.9k |
| SubagentHandback | 2 | 5.9k |
| Write | 1 | 4.7k |
| Agent | 3 | 1.7k |
| (no tool) | 0 | 1.6k |
| Read | 4 | 465 |
| Monitor | 1 | 328 |
| ToolSearch | 2 | 275 |
| TaskStop | 1 | 109 |
| **Total** | 111 | 60.9k |
