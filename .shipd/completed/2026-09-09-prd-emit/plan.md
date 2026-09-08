# prd-emit
Status: verified
Epic: prd-discovery

## Idea

Give PRDs their write and read paths: a staged `spec_emit.py prd` install
verb, a `cat prd` mediated read, and a `prd` surface in the `search` corpus.

### Motivation

The PRD store, registry, and lint shipped with `prd-store`, but nothing can
install or read a PRD through the engine yet — and the epic mandates one
staged write path with the wiki/initiative discipline before the `/s:prd`
skill can exist.

### Details

- `spec_emit.py prd <slug> --from <file> [--replace]` — staged,
  validate-then-install into the workspace's `prds/<slug>/prd.md`.
- `spec_status.py cat prd <slug>` — workspace-chain read.
- `search` gains kind `prd` beside the `initiative` surface.

Affected capabilities: `spec-io` (modified `staged-emission`,
`mediated-read-verb`), `spec-status` (modified `search-verb`). Impact:
`plugins/s/skills/build/scripts/spec_emit.py`,
`plugins/s/skills/build/scripts/spec_status.py`, tests
`test_spec_emit.py`/`test_spec_status.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump). No new dependencies.

### Non-goals

- No new curated binary verb, no `LIST_KINDS` entry, and no `workspace-show`
  roster change — deliberate surface parity with initiatives, which have
  none of those either; binary exposure rides the already-curated
  `shipd search`.
- No `/s:prd` skill, no `PRD:` epic line, no PRD status transitions — later
  members.
- No change to `related`, whose contract stays byte-for-byte.

## Implementation

- **`emit_prd(root, slug, src, replace)`** in `spec_emit.py`, a line-for-line
  mirror of `emit_initiative` (`spec_emit.py:153-175`): refuse a missing
  source file; `sc.find_workspace_root(root)` with the error
  `no workspace found from <abs>; \`prd\` requires a discoverable workspace
  root` when `None`; destination `sc.prd_path(ws_root, slug)`; validation
  callback running `sl.lint_prd(ws_root, slug, errors)`; installation through
  the existing `_install_dir` (backup, install, validate, byte-for-byte
  restore on findings, `--replace` refusal on an existing destination).
  Argparse: `p_prd = sub.add_parser("prd", …)` mirroring the `initiative`
  parser, dispatched from the same `args.mode` chain, and the module
  docstring's mode list gains the `prd` entry. Rejected: a bespoke installer
  — `_install_dir` is the one staged-write seam.
- **`cat prd <slug>`** in `spec_status.py`'s `cmd_cat`
  (`spec_status.py:2728-2777`), mirroring the `initiative` branch: resolve
  the workspace (for the error's expected path via
  `sc.prd_path(ws_root, slug)`), resolve the content with
  `sc.resolve_prd(root, slug)` (nearest chain member wins), print through
  `_cat_files`, and error `prd '<slug>' not found (<expected>)` on `None`.
  The `cat` argparse kind choices and docstring gain `prd`.
- **Search surface**: `_search_prd_artifacts(root)` beside
  `_search_initiative_artifacts`, identical shape — anchor via
  `sc.resolve_wiki_root(root)`, records
  `("prd", slug, prd_path, [prd_path])` for each `prds/<slug>/prd.md`,
  `[]` on any `ConfigError`/`OSError`/`None`. `cmd_search`'s corpus adds it
  after the initiative surface. No dedup concern: kind `prd` collides with
  nothing.
- **Tests.** `test_spec_emit.py`: a lint-clean PRD installs (exit 0, file at
  the workspace path); an invalid PRD (missing tier section) prints findings,
  installs nothing, exits non-zero; a pre-existing destination refuses
  without `--replace` and replaces with it; no-workspace errors. Reuse the
  suite's existing temp-workspace fixtures. `test_spec_status.py`: `cat prd`
  prints content with the separator via a chain member; unknown slug errors
  naming the expected path; `SearchTest` gains a PRD-surface case (kind
  `prd` block) and a no-workspace degradation case stays green.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` to the next free
  patch at build time (`0.6.195` — main consumed `.192`–`.194` while this
  change was in flight).
- **Risk**: none novel — every seam (`_install_dir`, `resolve_prd`,
  `lint_prd`, the search render tail) already exists and is tested; this
  change only wires them together, so the main failure mode is drift from
  the initiative mirror, which the tests pin.
