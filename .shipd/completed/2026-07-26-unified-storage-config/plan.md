# unified-storage-config
Status: verified

## Idea

The engine scatters its storage across three inconsistent conventions: a
visible `am/` directory in repos, `.shipd/` dot-dirs at both workspace and
repo level (marker/registry and git-ignored state), initiative briefs and
project context polluting the workspace root (`<ws>/initiatives/`,
`<ws>/projects/`), and `~/.shipd/` for build config and logs. Every path is
hardcoded; nothing is configurable; and skills construct storage paths from
convention, so any layout change breaks them silently.

This change unifies everything on one convention:

- All content lives in a `.shipd/` directory (hidden — specs stay checked in but
  users interact through skills), at repo level (`verified/planned/completed/
  epics/state.json`) and workspace level (`initiatives/`, `projects/`).
- All configuration lives in `.shipd-config.json` files resolved by upward search
  with layered per-key merge and built-in defaults.
- The directory name is a config key (`dir`, default `.am`).
- `.shipd/` and `am/config.json` are retired; `~/.shipd/` becomes
  `~/.shipd-config.json` + `~/.shipd/builds/`.
- A new `spec_emit.py` (stage → validate → install) plus `cat`,
  `config-show`, and `epic-set-initiative` verbs make the engine the single
  interface for every spec read and write, so skills never construct paths.
- This repo migrates: `git mv am .am`, themes fold into a root
  `.shipd-config.json`.

### Non-goals

- No legacy fallback: the engine never probes `.shipd/` or an unconfigured
  `am/`; existing layouts are migrated, not dual-supported.
- No change to the spec grammar itself (requirements, deltas, hashes).
- No config resolution in `statusline.sh` — it stays POSIX bash and assumes
  the default `.am` name (documented limitation for renamed dirs).
- No epic decomposition; this ships as one coordinated cutover.

Affected capabilities: `shipd-config` (added), `spec-io` (added); modified:
`shipd-workspace`, `shipd-spec-format`, `shipd-spec-lint`, `spec-status`, `statusline`,
`build-reporting`, `shipd-plan`, `shipd-initiative`, `project-readme`. Impact: all
four engine scripts + `spec_emit.py` (new), their tests and fixtures,
`statusline.sh`, `evals/run.py` + eval fixtures, every skill doc under
`plugins/s/skills/`, the repo's own `am/` → `.shipd/` rename, plugin version
bump.

## Implementation

- **Fixed config anchor.** The filename `.shipd-config.json` is a constant
  (`spec_common.CONFIG_FILENAME`); the `dir` key renames the content
  directory, never the config file — otherwise discovery could not bootstrap.
- **Layered discovery.** `resolve_config(start)` walks start → filesystem
  root collecting `.shipd-config.json` files, appends `~/.shipd-config.json` as the
  outermost layer when home is not already in the chain, then built-in
  defaults. Merge is shallow, top-level, per key: the nearest layer declaring
  a key wins it wholesale. Rejected: first-found-wins (repo config would
  shadow the workspace's); deep merge (opaque provenance).
- **Workspace = config with a `workspace` key.** The nearest ancestor whose
  own `.shipd-config.json` declares `workspace` is the workspace root; that
  object is the registry (same `projects` shape as today). The `workspace`
  key never merges across layers. `init_workspace` writes
  `{"workspace": {}}`, preserving other keys when the file already exists.
- **Content dir resolution.** `specs_dirname(config)` returns `dir` (default
  `.am`; must be a single path component). Repo paths resolve through the
  repo's layered config; workspace content (`<ws>/<dir>/initiatives/`,
  `<ws>/<dir>/projects/`) through the workspace root's. Session state moves
  to `<dir>/state.json`, git-ignored.
- **`spec_emit.py` (new script).** `change <name> --from <staging-dir>`,
  `initiative <slug> --from <file>`, `epic <slug> --from <file>`: copy into
  the resolved destination, run the existing lint checks in-process, and on
  any finding remove what was installed and exit non-zero — an invalid spec
  never lands. Existing destinations are refused without `--replace`.
  Rejected: validate-in-staging (lint needs real tree context, e.g. base
  hashes and epic references).
- **Mediated reads.** `spec_status.py cat change|verified|epic|initiative
  <slug>` prints content with `--- <relpath>` separators. `config-show`
  prints each resolved key with the file that supplied it, the content dir,
  and the workspace root. `epic-set-initiative <epic> <initiative>` writes
  the `Initiative:` header line metadata-preservingly, so no skill edits an
  epic header by hand.
- **Path notation for older specs.** Literal `am/` prefixes remaining in the
  master library denote the configured content dir (shipd-config
  `spec-library-path-notation`); definitional requirements are rewritten in
  this change, incidental mentions are covered by the notation rule.
- **Statusline.** Reads default `.shipd/planned` and `.shipd/state.json` directly;
  the constitution forbids spawning Python from it, so it does not resolve
  config. A repo that renames the dir loses statusline rendering only.
- **Migration.** This repo: `git mv am .am`, root `.shipd-config.json` with
  `valid_themes`, delete `am/config.json`, gitignore `.shipd/state.json`, update
  test/eval fixtures and `evals/run.py` assertions. Live workspace
  `~/projects`: convert `.shipd/workspace.json` → `.shipd-config.json`
  `workspace` section, move `initiatives/` under `.shipd/`, delete `.shipd/`.
  Plugin version bumps to 0.3.0 (breaking layout change).

Risks: a missed hardcoded path (guard: repo-wide grep task for
`.shipd|am/planned|am/verified|am/completed|am/epics|am/config` plus the
full test suite and a library lint on the migrated tree); skills drifting
back to direct writes (guard: `engine-mediated-skill-access` requirement +
doc sweep); statusline blind to renamed dirs (accepted, documented).
