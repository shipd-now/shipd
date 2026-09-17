## MODIFIED Requirements

### Requirement: Registry data
id: registry-data
base: b8578dcdf086

The engine SHALL provide a stdlib-only module `plugins/s/skills/build/scripts/harness_registry.py` declaring `FEATURES` — exactly the vocabulary `subagents`, `question-dialogs`, `file-references`, `background-tasks` — and `HARNESSES`, fifteen harness entries (`claude-code`, `cursor`, `github-copilot`, `windsurf`, `aider`, `codex`, `cline`, `roocode`, `continue`, `antigravity`, `agy`, `devin`, `oh-my-pi`, `opencode`, `pi`) each carrying a unique kebab-case `id`, display `name`, `repo_pattern`, `user_dir`, supported `dialect`, `frontmatter` tuple, and `features` tuple that is a subset of `FEATURES`.

For every dialect other than `conventions-file`, a non-`None` `repo_pattern` SHALL contain a `{command}` placeholder; a `conventions-file` pattern SHALL be a literal path. A `user_dir` MAY contain `{command}` when each command requires its own directory. The `aider` entry's pattern SHALL remain `shipd-conventions.md`. The module SHALL expose `get(id)` and ordered `ids()` accessors.

The module SHALL declare data-driven legacy user patterns for generated surfaces that moved. AGY's legacy pattern SHALL identify `~/.gemini/antigravity-cli/skills/shipd-{command}.md`.

#### Scenario: Every entry is structurally valid
- **WHEN** the test suite iterates `HARNESSES`
- **THEN** every entry satisfies the registry's id, key, dialect, frontmatter, path-placeholder, and feature-vocabulary invariants

#### Scenario: Known entries carry their researched paths
- **WHEN** `get` is called for `cursor`, `github-copilot`, and `codex`
- **THEN** cursor's repo pattern is `.cursor/commands/shipd-{command}.md`, GitHub Copilot's ends with `.prompt.md`, and Codex has no repo pattern and a user directory under `~/.codex/prompts`

#### Scenario: AGY CLI carries its researched skill surfaces
- **WHEN** `get("agy")` is read
- **THEN** its name is `Antigravity CLI`, its repo pattern is `.agents/skills/shipd-{command}/SKILL.md`, its user directory is `~/.gemini/config/skills/shipd-{command}/`, its dialect is `yaml` with frontmatter `("name", "description")`, and its features are exactly `subagents`, `file-references`, and `background-tasks`

#### Scenario: AGY CLI and Antigravity remain separate entries
- **WHEN** `ids()` is read
- **THEN** it contains both `antigravity` and `agy`, and their repo patterns differ

#### Scenario: OpenCode carries its researched paths
- **WHEN** `get("opencode")` is read
- **THEN** its repo pattern is `.opencode/commands/shipd-{command}.md`, its user directory is `~/.config/opencode/commands/`, its dialect is `yaml` with frontmatter `("description",)`, and its features are exactly `subagents` and `file-references`

#### Scenario: Pi carries its researched paths
- **WHEN** `get("pi")` is read
- **THEN** its repo pattern is `.pi/prompts/shipd-{command}.md`, its user directory is `~/.pi/agent/prompts/`, its dialect is `yaml` with frontmatter `("description", "argument-hint")`, and its only feature is `file-references`

#### Scenario: Pi and oh-my-pi are separate entries
- **WHEN** `ids()` is read
- **THEN** it contains both `oh-my-pi` and `pi`, with repo patterns `.omp/commands/shipd-{command}.md` and `.pi/prompts/shipd-{command}.md` respectively

#### Scenario: Claude Code declares the full feature set
- **WHEN** `get("claude-code")` is read
- **THEN** its features equal the complete `FEATURES` vocabulary, while aider declares none

#### Scenario: Unknown id returns None
- **WHEN** `get("no-such-harness")` is called
- **THEN** it returns `None` and `ids()` does not contain that id
