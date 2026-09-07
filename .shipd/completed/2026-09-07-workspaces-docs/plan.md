# workspaces-docs
Status: verified

## Idea

Rename the portable-workspaces guide to plain "workspaces", make its example
layout coherent under a single `~/workspaces/` convention, and give the
`shipd` binary the `workspace init`/`workspace sync`/`wiki init`/`config`
verbs the guide's commands need so the docs can stop invoking engine scripts
by path.

### Motivation

The guide's "portable" name is the delivery epic's internal slug
(`.shipd/epics/portable-workspaces`) leaked into user-facing docs, and its
examples mix three directory conventions (`~/jobs/…`, `~/projects/jobs/…`)
without ever saying which folder is the workspace repo. Worse, every
interactive command is a raw `python3 <plugin>/skills/build/scripts/…`
invocation because the `shipd` binary cannot express them — `shipd workspace`
maps only to `workspace-show`.

### Details

- Extend `plugins/s/bin/shipd`: mode words `init`/`sync` on the `workspace`
  verb, a new `wiki` verb (bare → `wiki-show`, `init` → `wiki-init`), and a
  new `config` verb (→ `config-show`), with banner and docstring updates.
- `git mv docs/portable-workspaces.md docs/workspaces.md`; retitle, drop the
  "portable" term, rewrite the examples to one `~/workspaces/<job>/`
  convention, and switch every interactive command to the `shipd` binary.
  The headless-consumers section keeps the raw `spec_status.py` footprint.
- Update the two inbound references: the `docs/oracle.md` link and the
  `spec_common.py` sync-ladder comment.

Affected capabilities: `shipd-cli` (modified), `shipd-workspace` (doc
requirement re-issued). Impact: `plugins/s/bin/shipd`,
`plugins/s/skills/build/tests/test_shipd_cli.py`, `docs/workspaces.md`,
`docs/oracle.md`, `plugins/s/skills/build/scripts/spec_common.py` (comment
only), `plugins/s/.claude-plugin/plugin.json` (version bump).

### Non-goals

- No change to the engine verbs' own behavior — `workspace-init`,
  `workspace-sync`, `wiki-init`, and `config-show` semantics are untouched;
  the binary only dispatches to them.
- No change to the headless-consumer contract (bare clone + Python 3 +
  `spec_status.py` run in place) — the shipd-app SaaS pins that footprint,
  so the guide's headless section keeps naming the script, not the binary.
- No rename of the completed `portable-workspaces` epic or any historical
  spec artifact — only the live doc and its inbound references.
- No mutating spec-library verbs exposed through the binary — `workspace
  init`/`sync` and `wiki init` write user-domain files only (a config
  marker, a managed `.gitignore` block, a wiki scaffold), never a spec
  artifact.

## Implementation

- **Mode-word dispatch mirrors the board/render precedent** in `bin/shipd`
  (and the `worktree` subverb handling): the first trailing argument is
  consumed when it is a known bare word, anything else falls through to the
  default delegate with all arguments intact. `shipd workspace init …` →
  `spec_status.py workspace-init …`, `shipd workspace sync …` →
  `workspace-sync …`, else `workspace-show`; `shipd wiki init …` →
  `wiki-init …`, else `wiki-show`; `shipd config` → `config-show` (a plain
  table mapping, no mode words). Rejected: hyphenated top-level verbs
  (`shipd workspace-init`) — the banner stays small and the subverb shape
  matches the existing verbs.
- **Constitution fit:** the three writing delegates touch user-domain files
  only, so they join the binary docstring's explicit-word exceptions list;
  everything else stays a read/inspect verb.
- **Runnable premises verified** (all observed, exit 0): `spec_status.py
  workspace-init --help` (positional `path`, `--git`, `--nested`);
  `workspace-sync --help` (`--json`, `--write-gitignore`); `wiki-init
  --help` (`--personal`); `config-show` prints the resolved `dir`/`store`
  lines; `shipd help` today lists no `wiki`/`config` verb and maps
  `workspace` to `workspace-show` only. `workspace-show --help` takes no
  positionals, so the new mode words shadow nothing.
- **Doc convention:** workspace repos live in a `~/workspaces/` parent, one
  folder per job — the running example becomes
  `~/workspaces/documents-linking/`. The leaf keeps the job name rather than
  the focus-project name so it cannot be confused with the member repo
  `documents/` materialized inside it. The nesting section files the nested
  job under its base workspace root with the same annotation style, and the
  layout diagram labels the workspace repo's role explicitly.
- **Rename via `git mv`** to preserve history; the guide keeps its section
  structure (setup, create, git, load, day-to-day, nesting, external store,
  team sharing, headless) so inbound anchors mostly survive.
- **Spec delta shape:** `shipd-cli`'s `cli-dispatch` is MODIFIED (base
  `53c0e4a0f88b`) to add the two verbs and the workspace/wiki mode
  mappings. `shipd-workspace` re-issues the doc mandate as a REMOVED
  (`portable-workspaces-doc`, base `99281c99a78c`) + ADDED
  (`workspaces-doc`) pair rather than RENAMED, because both the id and the
  content change and the pair keeps the merge unambiguous.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` → `0.6.185` — the
  cache snapshot is keyed by version, so binary edits without a bump would
  keep sessions on stale verbs.

Risk: external deep links to `docs/portable-workspaces.md` break — the only
in-repo links are `docs/oracle.md` and a code comment, both updated here;
accepted for anything outside the repo.
