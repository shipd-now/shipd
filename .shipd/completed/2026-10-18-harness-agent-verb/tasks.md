## 1. Agent files ride the write pipeline

- [x] 1.1 [req: harness-add-remove, harness-status] In
      `plugins/s/skills/build/tests/test_harness_generate.py`, add tests
      against a temp root and an isolated `HOME`: `shipd harness add
      claude-code --user` writes one owned agent file per `hr.AGENT_ROLES`
      member under the harness's user agent directory, each carrying the
      ownership marker, and an unchanged rerun writes nothing; `shipd harness
      add cursor --user` writes no agent file; `shipd harness remove
      claude-code --user` deletes the agent files and prunes the emptied
      directory; an unmarked file at a harness's agent path makes `add` exit
      nonzero without `--force` and leaves the file unchanged; and `status`
      reports `installed` after an add, then `stale` once one agent file is
      deleted. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -p 'test_harness_generate.py'`
      and observe the new tests fail.
- [x] 1.2 [req: harness-add-remove, harness-status] In
      `plugins/s/skills/build/scripts/harness_generate.py`, add
      `agent_paths(entry, mode, root)` returning one path per `AGENT_ROLES`
      member via `agent_repo_relpath`/`agent_user_path` (empty when the entry
      has no agent surface) and `_agent_payloads(entry, mode, root, base_dir)`
      pairing each path with `render_agent(entry, role, base_dir)`. Extend
      `planned` to append the agent payloads for every entry, `remove`'s
      candidate list to include the agent paths, and `_entry_state`'s payload
      list to include the agent payloads so `expected`, `present`, and the
      currency check cover them.

## 2. The verb reports the agent member

- [x] 2.1 [req: harness-add-remove] In `plugins/s/bin/shipd`, add `"agent"` to
      `HARNESS_FIELDS` and extend `_harness_field` so a dict renders as its
      `repo_pattern` value, falling back to `none`. In
      `plugins/s/skills/build/tests/test_harness_registry.py`, add a test that
      `shipd harness show claude-code` prints `.claude/agents/shipd-{agent}.md`
      and that `shipd harness show cursor` prints `none` for the agent field.

## 3. Version bump

- [x] 3.1 [req: *] In `plugins/s/.claude-plugin/plugin.json`, change `version`
      from `0.6.322` to `0.6.323`.

## 4. Verify

- [x] 4.1 [req: *] Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -p 'test_harness_generate.py'`,
      then the whole `python3 -m unittest discover -s plugins/s/skills/build/tests`;
      both exit 0. Run
      `python3 plugins/s/skills/build/scripts/spec_lint.py harness-agent-verb`
      and confirm it prints `OK`. In a temp directory, run `shipd harness add
      claude-code --user` with an isolated `HOME` and confirm the agent files
      appear, then `shipd harness remove claude-code --user` and confirm they
      are gone.
