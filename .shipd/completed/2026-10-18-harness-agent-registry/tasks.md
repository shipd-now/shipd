## 1. Neutral agent source

- [x] 1.1 [req: registry-agent-source] In
      `plugins/s/skills/build/tests/test_harness_registry.py`, add a test class
      that reads `plugins/s/harness/agents/` and asserts it holds exactly one
      `.md` file per `hr.AGENT_ROLES` member, that each file's first non-blank
      line is a non-empty `<!-- description: ... -->` marker, and that the text
      after the marker equals the body of `plugins/s/agents/<role>.md` after
      its YAML frontmatter. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -p 'test_harness_registry.py'`
      and observe the new test fail.
- [x] 1.2 [req: registry-agent-source] Create
      `plugins/s/harness/agents/sub-agent.md`,
      `plugins/s/harness/agents/oracle.md`, and
      `plugins/s/harness/agents/validator.md`. Each file opens with
      `<!-- description: <the plugin agent's own description> -->`, then a
      blank line, then the body of `plugins/s/agents/<role>.md` with its YAML
      frontmatter removed, copied verbatim.

## 2. Registry agent data

- [x] 2.1 [req: registry-data] In
      `plugins/s/skills/build/tests/test_harness_registry.py`, add `"agent"` to
      `ENTRY_KEYS`, then add tests asserting: every entry's `agent` is `None`
      or a dict whose keys are exactly `{repo_pattern, user_dir, dialect,
      frontmatter, extra}`; `agent` is non-`None` exactly when the entry
      declares `subagents`; a non-`None` `repo_pattern` contains `{agent}`;
      `dialect` is a member of `hr.AGENT_DIALECTS`; `frontmatter` is an
      ordered, duplicate-free subset of `("name", "description")`; `extra` is a
      tuple of `(str, str)` pairs; and `agent_surface` returns `None` for a
      non-`subagents` harness. Pin the four researched agent targets:
      `claude-code` `.claude/agents/shipd-{agent}.md` with user directory
      `~/.claude/agents/` and frontmatter `("name", "description")`;
      `opencode` `.opencode/agents/shipd-{agent}.md` with
      `~/.config/opencode/agents/`, frontmatter `("description",)`, and extra
      `(("mode", "subagent"),)`; `agy` `.agents/agents/shipd-{agent}.md` with
      `~/.gemini/config/agents/`, frontmatter `("name", "description")`, and
      extra `(("subagent", "true"),)`; `oh-my-pi` `.omp/agents/shipd-{agent}.md`
      with `~/.omp/agent/agents/` and frontmatter `("name", "description")`.
      Run the suite and observe the new tests fail.
- [x] 2.2 [req: registry-data] In
      `plugins/s/skills/build/scripts/harness_registry.py`, add
      `AGENT_DIALECTS = ("yaml",)` and
      `AGENT_ROLES = ("sub-agent", "oracle", "validator")` beside `FEATURES`;
      add an `agent` member to every `HARNESSES` entry — the four researched
      dicts above, `None` for the other eleven — and add
      `agent_surface(harness_id)` returning the entry's `agent` member or
      `None`, beside `get` and `ids`. Update the module docstring's key list to
      name `agent`.

## 3. Version bump

- [x] 3.1 [req: *] In `plugins/s/.claude-plugin/plugin.json`, change `version`
      from `0.6.320` to `0.6.321`.

## 4. Verify

- [x] 4.1 [req: *] Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -p 'test_harness_registry.py'`
      and then the whole `python3 -m unittest discover -s plugins/s/skills/build/tests`;
      both exit 0. Run
      `python3 plugins/s/skills/build/scripts/spec_lint.py harness-agent-registry`
      and confirm it prints `OK`. Confirm `shipd harness show claude-code`
      still runs and its output is unchanged for a harness with no agent
      surface.
