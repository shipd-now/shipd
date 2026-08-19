# harness-registry

### Requirement: Registry data
id: registry-data

The engine SHALL provide a stdlib-only module
`plugins/s/skills/build/scripts/harness_registry.py` declaring `FEATURES` —
exactly the vocabulary `subagents`, `question-dialogs`, `file-references`,
`background-tasks` — and `HARNESSES`, twelve harness entries (`claude-code`,
`cursor`, `github-copilot`, `windsurf`, `aider`, `codex`, `cline`,
`roocode`, `continue`, `antigravity`, `devin`, `oh-my-pi`) each carrying:
a unique kebab-case `id`, a display `name`, a `repo_pattern` (repo-relative
generated-file path containing a `{command}` placeholder, or `None`), a
`user_dir` (user-global command directory or `None`), a `dialect` (one of
`yaml`, `markdown-headers`, `conventions-file`), a `frontmatter` field
tuple (empty for non-`yaml` dialects), and a `features` tuple that SHALL be
a subset of `FEATURES`. The module SHALL expose `get(id)` returning the
entry or `None` and `ids()` returning the ordered id tuple.

#### Scenario: Every entry is structurally valid
- **WHEN** the test suite iterates `HARNESSES`
- **THEN** every id is unique kebab-case, every `features` value is a subset
  of `FEATURES`, every non-`None` `repo_pattern` contains `{command}`, and
  every non-`yaml` dialect has an empty `frontmatter` tuple

#### Scenario: Known entries carry their researched paths
- **WHEN** `get` is called for `cursor`, `github-copilot`, and `codex`
- **THEN** cursor's `repo_pattern` is `.cursor/commands/shipd-{command}.md`,
  github-copilot's ends with `.prompt.md`, and codex has `repo_pattern`
  `None` with a `user_dir` under `~/.codex/prompts`

#### Scenario: Claude Code declares the full feature set
- **WHEN** `get("claude-code")` is read
- **THEN** its `features` equal the whole `FEATURES` vocabulary, and
  aider's `features` and `repo_pattern` are empty/`None`

#### Scenario: Unknown id returns None
- **WHEN** `get("no-such-harness")` is called
- **THEN** it returns `None` and `ids()` does not contain the id

### Requirement: Harness read verbs
id: harness-read-verbs

The `shipd` binary SHALL provide a `harness` verb whose read actions are
read-only: bare or with `list` it SHALL print one line per registry entry;
with `show <id>` it SHALL print every field of that entry; with `--json` it
SHALL instead emit one machine-readable JSON document (the entry list, or
the single entry for `show`). If `show` names an unknown id, then the
binary SHALL print a single `Error: <reason>` line on stderr and exit
nonzero. The `list` and `show` actions SHALL create or modify no files;
the verb's writing actions (`add`, `remove`) are governed by the
`harness-verb` capability.

#### Scenario: List names every harness
- **WHEN** `shipd harness` runs
- **THEN** stdout contains all twelve registry ids and the exit code is 0

#### Scenario: Show prints one entry's data
- **WHEN** `shipd harness show cursor` runs
- **THEN** stdout contains `.cursor/commands/shipd-{command}.md` and the
  entry's dialect, and the exit code is 0

#### Scenario: JSON is machine-readable
- **WHEN** `shipd harness --json` runs
- **THEN** stdout parses as JSON with twelve entries whose ids match `ids()`

#### Scenario: Unknown id is a single-line error
- **WHEN** `shipd harness show no-such-harness` runs
- **THEN** stderr carries a single line beginning `Error: ` and the exit
  code is nonzero

#### Scenario: The read actions write nothing
- **WHEN** `shipd harness` and `shipd harness show cursor` run in a
  temporary directory
- **THEN** the directory's contents are unchanged afterwards
