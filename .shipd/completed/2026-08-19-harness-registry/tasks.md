## 1. Registry module

- [x] 1.1 [req: registry-data] Add
      `plugins/s/skills/build/tests/test_harness_registry.py` (unittest
      style) covering the registry data: every `HARNESSES` id unique and
      kebab-case; every `features` tuple a subset of `FEATURES` (which must
      equal exactly `("subagents", "question-dialogs", "file-references",
      "background-tasks")`); every non-None `repo_pattern` contains
      `{command}`; every non-`yaml` dialect has an empty `frontmatter`;
      `get("cursor")["repo_pattern"] ==
      ".cursor/commands/shipd-{command}.md"`; github-copilot's pattern ends
      `.prompt.md`; codex has `repo_pattern is None` and a `user_dir` under
      `~/.codex/prompts`; claude-code's features equal the full vocabulary;
      aider has empty features and `repo_pattern is None`;
      `get("no-such-harness") is None`. Run the file and observe it fail —
      the module does not exist yet.
- [x] 1.2 [req: registry-data] Add
      `plugins/s/skills/build/scripts/harness_registry.py`: `FEATURES`,
      `HARNESSES` with the twelve entries exactly as tabled in `plan.md`'s
      `## Implementation`, and the `get(id)` / `ids()` accessors.
      Stdlib-only, no imports beyond the standard library.

## 2. Read verbs

- [x] 2.1 [req: harness-read-verbs] Extend
      `plugins/s/skills/build/tests/test_harness_registry.py` with verb
      tests against the real binary (`plugins/s/bin/shipd`, subprocess, the
      existing `test_shipd_cli.py` conventions): `shipd harness` exits 0 and
      stdout contains all twelve ids; `shipd harness show cursor` exits 0
      and contains `.cursor/commands/shipd-{command}.md`;
      `shipd harness --json` parses as JSON with twelve entries matching
      `ids()`; `shipd harness show no-such-harness` exits nonzero with a
      single `Error: ` line on stderr; running the verbs in a temp cwd
      leaves it unchanged. Run and observe the new tests fail.
- [x] 2.2 [req: harness-read-verbs, cli-dispatch] In `plugins/s/bin/shipd`
      add `cmd_harness(args)` (argparse: optional action `list`/`show`,
      optional id, `--json`), importing `harness_registry` via the binary's
      on-demand engine-import pattern; wire `harness` into `main`'s dispatch
      as an in-binary verb; add `harness [list|show <id>]` to the usage
      banner text and extend the banner's `--json` read-verb note to name
      it. Unknown id uses the inlined `_err` helper and returns nonzero.
- [x] 2.3 [req: *] Run the CI suite command
      `python3 -m unittest discover -s plugins/s/skills/build/tests -v`
      without `textual`/`pydantic` installed and observe all tests pass,
      including the existing `test_shipd_cli.py` usage-banner tests.

## 3. Ship the snapshot

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` to
      `0.6.139` (shipd-wordmark holds `0.6.138`; its merge precedes this
      build via the supersession gate's base-branch merge).

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 59 | 27.0k |
| Write | 5 | 13.9k |
| Edit | 12 | 10.6k |
| (no tool) | 0 | 5.3k |
| Read | 16 | 2.3k |
| Agent | 2 | 630 |
| Skill | 1 | 159 |
| **Total** | 95 | 59.8k |
