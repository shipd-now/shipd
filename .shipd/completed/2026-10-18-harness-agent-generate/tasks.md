## 1. Agent source reader

- [x] 1.1 [req: agent-rendering] In
      `plugins/s/skills/build/tests/test_harness_generate.py`, add tests for
      `hg.agent_source`: reading `sub-agent` returns the source's declared
      description and its body; an unknown role raises `ValueError`; and a
      temporary base directory whose `<role>.md` lacks the opening
      `<!-- description: ... -->` marker raises a `ValueError` naming the file.
      Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -p 'test_harness_generate.py'`
      and observe the new tests fail.
- [x] 1.2 [req: agent-rendering] In
      `plugins/s/skills/build/scripts/harness_generate.py`, add an
      `agent_source(role, base_dir=None)` reader that reads
      `plugins/s/harness/agents/<role>.md`, requires its opening
      `<!-- description: ... -->` marker, and resolves to
      `(description, body)`; raise a `ValueError` naming the path when the file
      is absent or the marker is missing.

## 2. Agent render and surface paths

- [x] 2.1 [req: agent-rendering] In
      `plugins/s/skills/build/tests/test_harness_generate.py`, add tests:
      `render_agent(hr.get("claude-code"), "sub-agent")` opens with a `---`
      block carrying `name: shipd-sub-agent` and the source's description, then
      the ownership `MARKER`, then the source body;
      `render_agent(hr.get("opencode"), "oracle")` carries `mode: subagent` and
      `render_agent(hr.get("agy"), "validator")` carries `subagent: true`, each
      after the entry's declared fields; rendering `claude-code` for every
      `AGENT_ROLES` member yields a description and body equal to
      `plugins/s/agents/<role>.md`'s description and body;
      `agent_repo_relpath` and `agent_user_path` return the pinned paths for
      `claude-code` and `oh-my-pi`; and `render_agent`, `agent_repo_relpath`,
      `agent_user_basename`, and `agent_user_path` each return `None` for
      `cursor`. Run the suite and observe the new tests fail.
- [x] 2.2 [req: agent-rendering] In
      `plugins/s/skills/build/scripts/harness_generate.py`, add
      `render_agent(entry, role, base_dir=None)` — the head from the entry's
      agent `frontmatter` fields (`name` as `shipd-<role>`, `description` from
      `agent_source`) plus its `extra` pairs, all through `yaml_scalar`, then
      `MARKER`, then the body — and the helpers `agent_repo_relpath`,
      `agent_user_basename`, and `agent_user_path`, each resolving the entry's
      agent `repo_pattern`/`user_dir` and returning `None` when `entry["agent"]`
      is `None`.

## 3. Version bump

- [x] 3.1 [req: *] In `plugins/s/.claude-plugin/plugin.json`, change `version`
      from `0.6.321` to `0.6.322`.

## 4. Verify

- [x] 4.1 [req: *] Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -p 'test_harness_generate.py'`,
      then the whole `python3 -m unittest discover -s plugins/s/skills/build/tests`;
      both exit 0. Run
      `python3 plugins/s/skills/build/scripts/spec_lint.py harness-agent-generate`
      and confirm it prints `OK`.
