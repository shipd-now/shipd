# harness-registry
Status: verified
Epic: harness-install

## Idea

Add the harness-adapter registry to the engine — the feature vocabulary and
the per-harness adapter data every later generation step consumes — plus
read-only `shipd harness` verbs to inspect it.

### Motivation

The harness-install epic's generation pipeline starts from a registry that
declares each harness's identity, target paths, frontmatter dialect, and
supported features, but no such module exists in the engine; the epic fixes
the feature vocabulary's first cut during this member.

### Details

- New engine module `plugins/s/skills/build/scripts/harness_registry.py`:
  the canonical feature vocabulary and twelve harness entries as stdlib data.
- New curated read verb `shipd harness` (`list` default, `show <id>`,
  `--json`) in `plugins/s/bin/shipd`, writing nothing.
- Tests at `plugins/s/skills/build/tests/test_harness_registry.py`; plugin
  version bump.

Affected capabilities: `harness-registry` (added), `shipd-cli` (modified —
the curated-verb set gains `harness`). Impact:
`plugins/s/skills/build/scripts/harness_registry.py` (new),
`plugins/s/bin/shipd` (verb, dispatch, usage banner),
`plugins/s/skills/build/tests/test_harness_registry.py` (new),
`plugins/s/.claude-plugin/plugin.json` (version bump). No new dependencies.

### Non-goals

- No file generation, no writes to any harness directory, and no
  `harness add`/`remove` — that is the `harness-verb` member.
- No command bodies or templates — that is the `harness-command-bodies`
  member; the registry never embeds prompt content.
- No capability detection at runtime — features are declared registry data,
  per the epic's decision.
- No pydantic validation — entries are validated by the test suite only.

## Implementation

- **Module shape:** `harness_registry.py` is stdlib-only data plus small
  accessors. `FEATURES` is the tuple
  `("subagents", "question-dialogs", "file-references", "background-tasks")`
  — the epic's first-cut vocabulary, fixed here. `HARNESSES` is a tuple of
  dicts, one per harness, with exactly the keys: `id` (kebab-case, unique),
  `name` (display), `repo_pattern` (repo-relative generated-file path with a
  `{command}` placeholder, or `None` for a harness with no per-repo command
  files), `user_dir` (user-global command directory, `None` where the
  harness has none), `dialect` (one of `yaml`, `markdown-headers`,
  `conventions-file`), `frontmatter` (tuple of field names the dialect
  emits, empty for non-YAML dialects), and `features` (tuple, subset of
  `FEATURES`). Accessors: `get(id)` returning the entry or `None`, and
  `ids()` returning the ordered id tuple. Rejected: dataclasses — plain
  dicts match the engine's existing style (`vendor_layout`, pipeline
  entries) and keep the module trivially JSON-serializable.
- **The twelve entries** (paths grounded in OpenSpec's adapters and the
  harness docs; the epic's "eleven harnesses" splits Cline/Roo Code into two
  entries because their directories differ):

  | id | repo_pattern | user_dir | dialect | frontmatter | features |
  | --- | --- | --- | --- | --- | --- |
  | claude-code | `.claude/commands/shipd/{command}.md` | `~/.claude/commands/shipd/` | yaml | name, description, allowed-tools | all four |
  | cursor | `.cursor/commands/shipd-{command}.md` | `~/.cursor/commands/` | yaml | name, id, category, description | file-references, background-tasks |
  | github-copilot | `.github/prompts/shipd-{command}.prompt.md` | None | yaml | description | file-references |
  | windsurf | `.windsurf/workflows/shipd-{command}.md` | `~/.codeium/windsurf/global_workflows/` | yaml | description | file-references |
  | aider | None | None | conventions-file | (empty) | (empty) |
  | codex | None | `~/.codex/prompts/` | yaml | description, argument-hint | file-references |
  | cline | `.clinerules/workflows/shipd-{command}.md` | None | markdown-headers | (empty) | file-references |
  | roocode | `.roo/commands/shipd-{command}.md` | None | markdown-headers | (empty) | file-references |
  | continue | `.continue/prompts/shipd-{command}.prompt` | None | yaml | name, description, invokable | file-references |
  | antigravity | `.agent/workflows/shipd-{command}.md` | None | yaml | description | file-references |
  | devin | `.devin/workflows/shipd-{command}.md` | None | yaml | name, description, category, tags | file-references |
  | oh-my-pi | `.omp/commands/shipd-{command}.md` | None | yaml | description | subagents, file-references |

  The `{command}` placeholder and the `shipd-` name prefix (a `shipd/`
  subdirectory namespace on Claude Code, mirroring OpenSpec's `opsx`
  namespace dir) implement the epic's command-id prefix decision. Feature
  declarations are the conservative first cut; per the epic, refining them
  later is a registry edit, not a body rewrite.
- **Verb wiring:** a `cmd_harness(args)` in `plugins/s/bin/shipd` following
  the in-binary verb pattern (`cmd_list`'s on-demand `_load_engine` import
  style): bare or `list` prints one line per entry (`id`, name, dialect,
  feature count); `show <id>` prints every field of one entry; `--json`
  emits the machine-readable document instead (the entries verbatim; `show`
  emits one entry object). Unknown id → the convention's single
  `Error: unknown harness '<id>'` line, nonzero exit (observed today:
  `shipd harness` is a usage error, exit 2 — the new verb replaces that).
  The usage banner gains `harness [list|show <id>]` and its `--json` note.
  Rejected: a standalone engine-script CLI — the registry's only consumers
  are the binary and the later generation verb, both in-process.
- **Version bump:** `plugins/s/.claude-plugin/plugin.json` to `0.6.139`
  (the shipd-wordmark member holds `0.6.138`; its merge lands before this
  change builds, and the supersession gate's `origin/main` merge brings it
  in).

Risk: harness vendors move their command directories over time; the registry
is data, so a moved path is a one-entry edit, and the `harness-verb` member's
generation tests — not this member — are where a wrong path would surface
behaviorally.
