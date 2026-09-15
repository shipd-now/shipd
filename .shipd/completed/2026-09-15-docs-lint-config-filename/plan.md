# docs-lint-config-filename
Status: verified

## Idea

Teach `docs_lint.py` to reject a documentation page that names a shipd
configuration file the engine never reads.

### Motivation

`docs/semantic-review-reference.md` shipped naming `shipd.config.json`. The
engine resolves configuration only from `.shipd-config.json`
(`spec_common.CONFIG_FILENAME`), and `semdiff._lint_config` wraps its read in a
bare `except`, so a file under any other name degrades silently to the
defaults. A reader following that page would have configured nothing and seen
no error. The lint passed the page; a human reading it caught the name. Six
pages under `docs/` name the configuration file, so the class recurs.

### Details

- Add an artifact-name check to `docs_lint.py` reporting `shipd.config.json`
  and a dot-less `shipd-config.json` as errors.
- Leave `shipd.config.example.json` clean, because that sample file exists.
- Record the rule in the standard, the one canonical rules file.
- Bump the plugin version, because the change touches `plugins/s/`.

Affected capabilities: `shipd-document` (one modified requirement). Impact:
`plugins/s/skills/document/scripts/docs_lint.py`,
`plugins/s/skills/document/references/standard.md`,
`plugins/s/skills/document/tests/test_docs_lint.py`, and
`plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No check over any other artifact name — worktree paths, script names, skill
  names. Only the configuration filename, which is the one observed drift.
- No new severity level and no configuration key. The check errors, like every
  other mechanical rule the lint enforces.
- No edit to any page under `docs/`. Every page now names the file correctly,
  so this change adds the guard rather than fixing an instance.

## Implementation

- **An error, not a warning.** A page naming a file the loader ignores
  misconfigures its reader in silence, because `_lint_config` catches every
  exception and falls back to the defaults. Nothing surfaces. That silence is
  the reason the rule belongs in the lint rather than in review judgement, so
  the finding exits 1.

- **Two patterns, and only one of them is safe as a substring.**
  `shipd.config.json` never occurs inside `shipd.config.example.json`, so a
  plain search finds it without a false positive. A dot-less
  `shipd-config.json` is different: it occurs inside the *correct*
  `.shipd-config.json`, so it matches only when no dot, word character, or
  hyphen precedes it. Getting this boundary wrong flags every correct page in
  the corpus, so the tests pin both directions.

- **The check reads every line, code fences included.** A wrong filename in a
  fenced block misleads a reader exactly as prose does, so this check does not
  go through `collect_units`, which exists to strip fenced content from the
  prose checks. It is a new function called from `check_file`, beside
  `check_marker`.

- **The standard names the rule.** `references/standard.md` is the one
  canonical rules source, and the skill reads it before writing a word. A
  mechanical rule the lint enforces but the standard omits is a rule an author
  meets only as a failure.

- **Risk: the guard hard-codes a filename that could itself change.** If the
  engine ever renames `CONFIG_FILENAME`, this check flags the new correct name
  and passes the old wrong one. The scenario names `.shipd-config.json`
  explicitly, so the rename fails a scenario rather than passing unnoticed.
