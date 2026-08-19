## MODIFIED Requirements

### Requirement: Registry data
id: registry-data
base: 35f467c02ffb

The engine SHALL provide a stdlib-only module
`plugins/s/skills/build/scripts/harness_registry.py` declaring `FEATURES` —
exactly the vocabulary `subagents`, `question-dialogs`, `file-references`,
`background-tasks` — and `HARNESSES`, twelve harness entries (`claude-code`,
`cursor`, `github-copilot`, `windsurf`, `aider`, `codex`, `cline`,
`roocode`, `continue`, `antigravity`, `devin`, `oh-my-pi`) each carrying:
a unique kebab-case `id`, a display `name`, a `repo_pattern` (repo-relative
generated-file path, or `None`), a `user_dir` (user-global command
directory or `None`), a `dialect` (one of `yaml`, `markdown-headers`,
`conventions-file`), a `frontmatter` field tuple (empty for non-`yaml`
dialects), and a `features` tuple that SHALL be a subset of `FEATURES`.
For every dialect other than `conventions-file`, a non-`None`
`repo_pattern` SHALL contain a `{command}` placeholder; a
`conventions-file` dialect's `repo_pattern` is a literal single-file path.
The `aider` entry's `repo_pattern` SHALL be `shipd-conventions.md`. The
module SHALL expose `get(id)` returning the entry or `None` and `ids()`
returning the ordered id tuple.

#### Scenario: Every entry is structurally valid
- **WHEN** the test suite iterates `HARNESSES`
- **THEN** every id is unique kebab-case, every `features` value is a subset
  of `FEATURES`, every non-`None` `repo_pattern` of a non-`conventions-file`
  dialect contains `{command}`, every `conventions-file` entry's
  `repo_pattern` contains no `{command}`, and every non-`yaml` dialect has
  an empty `frontmatter` tuple

#### Scenario: Known entries carry their researched paths
- **WHEN** `get` is called for `cursor`, `github-copilot`, and `codex`
- **THEN** cursor's `repo_pattern` is `.cursor/commands/shipd-{command}.md`,
  github-copilot's ends with `.prompt.md`, and codex has `repo_pattern`
  `None` with a `user_dir` under `~/.codex/prompts`

#### Scenario: Claude Code declares the full feature set
- **WHEN** `get("claude-code")` is read
- **THEN** its `features` equal the whole `FEATURES` vocabulary, and
  aider's `features` are empty with `repo_pattern` `shipd-conventions.md`
  and `user_dir` `None`

#### Scenario: Unknown id returns None
- **WHEN** `get("no-such-harness")` is called
- **THEN** it returns `None` and `ids()` does not contain the id
