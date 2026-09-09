# prd-verb
Status: verified

## Idea

Give PRDs a first-class binary surface: `shipd prd <slug>` prints a PRD
report — header facts, resolved path with chain provenance, and the epics
citing it — and bare `shipd prd` lists the workspace's PRDs.

### Motivation

The discover phase shipped with no user-facing way to inspect a PRD: the
binary has no `prd` verb, listing was deliberately deferred at `prd-emit`,
and the user asked for the noun-verb surface (`shipd prd <slug>`) matching
`shipd epic`.

### Details

- New `prd-show [slug]` verb in `spec_status.py`: with a slug, the report;
  bare, the roster. Both with `--json`.
- New curated `prd` binary verb delegating to it; banner and `--json`
  read-verbs sentence updated.
- `docs/prd.md` gains the verb's coverage.

Affected capabilities: `shipd-prd` (added `prd-show-verb`, modified
`prd-user-docs`), `shipd-cli` (modified `cli-dispatch`). Impact:
`plugins/s/skills/build/scripts/spec_status.py`, `plugins/s/bin/shipd`,
`docs/prd.md`, tests `test_spec_status.py`/`test_shipd_cli.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump). No new dependencies.

### Non-goals

- No render mode word or flag — the report prints the resolved `path:`, and
  `shipd render <path>` composes; a mode word would break the binary's
  pure-delegation pattern.
- No cross-project epic scan: the reverse lookup covers the invocation
  root's universe (root + worktrees), the same boundary every read verb
  keeps.
- No board lane or TUI beyond what `shipd render` already provides.
- No change to `/s:prd`, the emit path, or `search`.

## Implementation

- **`cmd_prd_show(root, slug, as_json=False)`** in `spec_status.py`, beside
  the other show verbs, using the shared `_emit(data, lines, as_json)`
  report machinery `cmd_epic_show` uses:
  - **With a slug**: resolve content via `sc.resolve_prd(root, slug)`; on
    `None`, error `prd '<slug>' not found (<expected>)` with the expected
    path from `sc.prd_path(ws_root, slug)` (workspace resolved as `cat prd`
    does; no discoverable workspace errors with the no-workspace message).
    Parse the resolved file's header (reuse the linter's parsing approach:
    `Status:`/`Template:` from the first five non-blank lines,
    `Initiative:` via `sc.parse_plan_metadata`). Report lines:
    `<slug>: <status>`, `Template: <tier>`, `Initiative: <slug>` (only when
    present), `path: <resolved>` (relative inside the root, absolute
    outside — the `_related_path` convention), one
    `cited-by: <epic-slug> (<status>)` line per epic in the invocation
    universe whose header carries `PRD: <slug>` (epics enumerated exactly
    as `_related_candidate_artifacts` finds them across `candidate_roots`,
    metadata via `sc.parse_plan_metadata`, sorted by slug, deduped
    root-first), and `cited-by: none` when no epic cites it. JSON mode
    emits one object with `slug`, `status`, `template`, `initiative`
    (nullable), `path`, and `cited_by` (list of `{slug, status}`).
  - **Bare (no slug)**: list every `prds/<slug>/prd.md` across the
    workspace chain — nearest member winning per slug, matching
    `resolve_prd`'s shadowing — one line per PRD:
    `<slug>: <status> (<tier>)`, sorted by slug; `no PRDs` plus the
    resolved store path when the chain holds none; the no-workspace error
    when nothing resolves. JSON mode emits an array of
    `{slug, status, template}` objects. Unparseable header fields render
    as `?`, never raising — a malformed store file is a lint problem, not
    a listing crash.
- **Argparse**: `p_prd_show = sub.add_parser("prd-show", …)` with an
  optional positional `slug` (`nargs="?"`) and `_add_json_flag`; dispatch
  branch beside `epic-show`'s.
- **Binary**: `"prd": ("spec_status.py", ["prd-show"])` in `VERB_TABLE`; a
  banner line `prd [slug]` ("a PRD's report and citing epics; bare: the
  workspace's PRD roster") under `epic`'s; `prd` added to the trailing
  "read verbs … accept --json" sentence. Delegation is the standard exec
  passthrough — bare and slugged forms both ride the same mapping.
- **Docs**: `docs/prd.md` gains a short "Inspecting PRDs" section after the
  search section — the two invocations with trimmed example output, the
  reverse-lookup note (repo-universe epics only), and the render
  composition (`shipd render <path>` on the report's path line) — and the
  FAQ's storage answer names `shipd prd` beside `shipd search`. Command
  convention unchanged: binary-or-skill only.
- **Tests**: `test_spec_status.py` — report fields for a chain-hosted PRD
  (including `Initiative:` present/absent), the citing-epics lines from a
  worktree-hosted epic, `cited-by: none`, unknown slug error naming the
  expected path, bare listing with shadowing (nearest chain member's
  status wins), empty-store and no-workspace cases, `--json` shapes for
  both forms. `test_shipd_cli.py` — `prd` in the `VERBS` banner tuple plus
  a delegation case mirroring `related`/`search`'s (unknown slug's
  `Error:` line and exit code pass through).
- **Version bump** `plugins/s/.claude-plugin/plugin.json` to the next free
  patch (0.6.198 if main still sits at 0.6.197).
- **Risk**: the reverse lookup reads every epic file in the universe per
  invocation — bounded (epics are few and small) and identical in cost to
  `related`'s epic surface; accepted for an interactive read verb.
