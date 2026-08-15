# shipd-port
Status: complete
Theme: spec-engine

## Introduction

`shipd` was named for one person. The product it grew into is not personal:
a spec-driven harness with its own engine, delivery board, autopilot, workspace
layer, and knowledge store — now getting a real brand and a real domain,
`shipd.now`. The name has to follow, and the name is load-bearing in a way a
normal rebrand is not. `am` is not just a word in a README: it is the plugin
identity Claude Code installs and caches, the `/s:` invocation prefix on
sixteen skills and three agents, the `.shipd/` content directory the engine reads,
the `.shipd-config.json` filename that bootstraps layered config discovery, the
`am-*` capability slugs in the spec library, and the `~/.shipd/builds` and
`~/.shipd-memory` paths where telemetry and personal memory live. Every one of those
is a contract something depends on.

This epic ports the whole system into the new `shipd-now/shipd` repository under
the `s` namespace: `/s:plan` becomes `/s:plan`, `plugins/s/` becomes
`plugins/s/`, `.shipd/` becomes `.shipd/`, `.shipd-config.json` becomes
`.shipd-config.json`, `shipd-plan` becomes `shipd-plan`, and every brand string
becomes `shipd` / `shipd.now`. The port is mechanical in bulk and delicate at the
edges, so it is driven by a **checked-in, tested rename tool** rather than by
hand or by a one-shot `sed`: the tool is what makes a 788-file diff reviewable,
and what makes the port repeatable while shipd keeps moving.

`shipd` is left running and unrenamed. It is the source the port reads from
and it keeps working for its current sessions; nothing in this epic modifies
shipd's code, only adds this epic and its member change artifacts to
shipd's spec library.

Success criteria: `shipd-now/shipd` has green CI across all four test suites;
`spec_lint.py` passes over the whole ported library; the delivery board and
metrics derive the same numbers from the ported archive as shipd does; the
`s@shipd` plugin installs and `/s:plan` runs; and shipd plans, builds, reviews,
and ships its own next change end-to-end without touching shipd.

### Non-goals

- **Renaming shipd.** The existing repo, its plugin, its installed cache
  snapshot, and its `.shipd/` library stay exactly as they are. This is a port, not
  a migration — both exist afterward.
- **A migration path for existing installs.** No aliasing of `/s:` to `/s:`, no
  compatibility shim reading `.shipd-config.json` under the new engine, no importer
  for a `~/.shipd-memory` store. The one operator on this system moves by hand.
- **Building the shipd.now website.** The domain is recorded as a brand string in
  the README and the manifests. No site, landing page, or docs deployment is
  scaffolded here.
- **Porting `openspec/`.** The 49-file frozen bootstrap-era archive has no live
  consumer and stays behind in shipd.
- **New capability or behavior.** Nothing in the engine, skills, or board gains
  or loses a feature. A member change that finds a bug during the port files it;
  it does not fix it here.
- **Keeping the two repos in sync afterward.** The rename tool is re-runnable, but
  standing up a continuous shipd→shipd sync is out of scope.

## Decisions

- **Member changes are planned in shipd and shipped to shipd.** The new repo
  has no `.shipd/` layout and no working `/s:` plugin until this epic's members
  land, so it cannot host its own planning. Each member is planned as a normal
  shipd change (`/s:plan <member>`, own worktree, own branch, artifacts under
  `.shipd/planned/`), but its *implementation target* is `../shipd` and its
  deliverable is a **PR on `shipd-now/shipd`**. The shipd branch carries only
  the change artifacts and ships as an shipd PR alongside. The final member
  cuts shipd over to self-hosting, after which shipd plans its own work under
  `/s:`.

- **The port is driven by a checked-in, tested rename tool, not by hand.** 788
  tracked files, ~121 of them naming `shipd`, cannot be ported reliably or
  reviewably by manual editing or a loose `sed`. `tools/port.py` in shipd
  encodes the token map and the path map, runs dry-first, and is unit-tested
  against synthetic fixtures. Reviewers read the map, not the diff. Because the
  tool re-reads shipd's tree at run time, every file and capability count in
  this epic is a snapshot taken at authoring — indicative of scale, never a
  target a member should hard-code or assert against.

- **Substitution is ordered, longest-token-first, and boundary-aware.** `am` is a
  two-letter substring of ordinary English (`ambiguous`, `stream`, `param`) and
  of unrelated identifiers. The map matches only anchored forms — `/s:`,
  `s:oracle`, `.shipd-config.json`, `.shipd/`, `plugins/s/`, `s@shipd`,
  `~/.shipd-memory`, `~/.shipd/builds`, `SHIPD_WORKTREE_IDLE_MINUTES`, capability slugs
  `am-<name>` — never a bare `am`. Longer tokens are applied before shorter ones
  so `.shipd-config.json` is never partially rewritten by the `.am` rule. Any file
  still containing an unanchored match after a run is reported, not silently
  passed.

- **Capability slugs become `shipd-*`, not `s-*`.** `shipd-plan` → `shipd-plan`,
  `shipd-epic` → `shipd-epic`, and so on for all sixteen prefixed capabilities. The
  spec library is prose someone else may read; a one-letter prefix there is
  cryptic where the invocation prefix `/s:` is merely terse. The eighteen
  unprefixed capabilities (`build-*`, `delivery-*`, `spec-status`, `statusline`,
  …) are untouched. Requirement IDs inside specs are not capability-prefixed and
  do not change, but every `[req:]` reference and every delta-spec path across
  the 150 archived changes follows the folder rename.

- **`.shipd/completed/` is ported with its text rewritten; `openspec/` is dropped.**
  `metrics.py` and the delivery board read `completed/` for throughput, cycle-time
  percentiles, and the forecast, so the history must come across *and* must parse
  under the new names — a verbatim archive would contradict the live layout and
  fail a lint pass. `openspec/` has no consumer and stays in shipd.

- **The plugin's version line is unbroken: `s@shipd` continues from shipd's.**
  It is the same software with a new name, so it starts at one bump past
  whatever `plugins/s/.claude-plugin/plugin.json` reads *at the moment the
  identity member runs* — not a number pinned here. shipd stays in
  development while this epic is planned, so the member reads the source version
  and increments it rather than hard-coding one. Keeping the sequence means the
  bump-every-plugin-change rule and the cache-snapshot discipline carry over with
  no special case for a reset.

- **Green CI on the ported tree is the acceptance bar for the engine, not
  inspection.** All four suites (`tests`, `tests_textual`, `review/tests`,
  `video-ingest/tests`) plus the lint steps run in shipd's own `ci` workflow. A
  member is not done because the rename looks right; it is done because the tests
  the rename touched still pass under the new paths.

- **Personal and machine-level state is *not* migrated.** `~/.shipd-memory`,
  `~/.shipd/builds`, `~/.shipd-config.json`, and `~/.cache/shipd/tui-venv` have
  `shipd` counterparts in the ported engine, but they start empty. Telemetry
  history that matters lives in the repo's `completed/` archive, which is ported.

## Design

**Token and path map.** The port is one map applied two ways — to file *paths*
and to file *contents*:

```
paths                          contents (anchored forms only)
  plugins/s/    -> plugins/s/   /s:            -> /s:
  .shipd/           -> .shipd/      s:oracle       -> s:oracle
  .shipd-config.json-> .shipd-      s:sub-agent    -> s:sub-agent
                    config.json  s:validator    -> s:validator
  .shipd/verified/am-<n>/           s@shipd     -> s@shipd
    -> .shipd/verified/          shipd        -> shipd
       shipd-<n>/                Shipd        -> Shipd
  .shipd/completed/*/specs/am-<n>/  .shipd-config.json -> .shipd-config.json
    -> .../specs/shipd-<n>/      ~/.shipd-memory    -> ~/.shipd-memory
                                 ~/.shipd/builds    -> ~/.shipd/builds
                                 .cache/shipd -> .cache/shipd
                                 AM_WORKTREE_    -> SHIPD_WORKTREE_
                                   IDLE_MINUTES       IDLE_MINUTES
```

**The seams.** The port decomposes along dependency order — each stage is
independently verifiable and the next one needs it:

1. *The tool* stands alone. It is testable against synthetic fixtures with no
   reference to shipd's real tree, so it is a small, self-contained first PR
   that makes every later PR reviewable.

2. *The engine* (`plugins/s/`) is where the namespace constants actually live:
   `CONFIG_FILENAME`, `DEFAULT_DIR`, `DEFAULT_MEMORY_DIR`, `build.log_dir`,
   `tui_bootstrap.py`'s venv cache path, `worktree.sh`'s idle-window env var,
   `semdiff.py`'s cohort literal. It carries its own four test suites, so it
   proves itself the moment shipd's `ci` workflow runs. It lands before any
   content, because the content is only readable by the engine that parses it.

3. *The library* (`.shipd/`) is bulk — 34 verified capabilities, 150 archived
   changes, 8 epics, autopilot reports, research, video bundles — plus the
   sixteen `am-*` → `shipd-*` folder renames. Its acceptance is structural:
   `spec_lint.py` clean over everything, and `metrics.py` deriving numbers
   identical to shipd's. The vestigial `.shipd/state.json` (an
   OpenSpec-era `current_spec` marker with no live reader) is dropped here.

4. *Identity* is what makes `/s:` real. The marketplace manifest names `shipd`
   and points at `./plugins/s`; the plugin manifest names `s`, one bump past
   shipd's version as read at that moment;
   `.claude/settings.json` enables `s@shipd` and points the statusline at
   `plugins/s/integrations/statusline.sh`. Then the local install: register the
   marketplace, install the plugin, start a fresh session, confirm the skills
   load under `/s:`. This is deliberately separate from the engine port — a
   namespace that parses is not the same as a namespace Claude Code will load.

5. *Brand* is the human-facing layer over a system that already works: README
   (new ASCII banner, `shipd.now`, the `/s:` skill table), `AGENTS.md` /
   `CLAUDE.md` restated for shipd's own cache-snapshot and worktree discipline,
   `.shipd/README.md` and `constitution.md`, the board's brand block
   (`shipd delivery board` in `dashboard.py`), the statusline header, the three
   tracked files under `docs/`, and replacing shipd's throwaway README and
   Node-template `.gitignore`. The port reads *tracked* files only — untracked
   working-tree content in shipd (scratch research, recordings) does not
   cross over, and nothing here depends on it.

6. *Evals* are the LLM-facing gap the unit suites do not cover. The three cases'
   fixtures move to the `.shipd` layout and `run.py` drives `/s:plan` against the
   working-tree plugin. They cost real model spend and stay out of `ci`, matching
   shipd's rule.

7. *Self-hosting* is the proof. shipd creates a worktree with its own
   `worktree.sh`, plans a change with `/s:plan`, builds it, merges and archives
   it with its own `spec_merge.py`, runs `/s:review` to post the
   `semantic-review` gate, and auto-merges a PR — with branch protection and both
   required checks configured on `shipd-now/shipd`. Until that loop closes, the
   port is a copy, not a system.

**Why this order and not the obvious one.** Brand is last-but-two rather than
first because rewriting README prose against a tree that is still moving wastes
the work; identity comes after the engine because an install that loads broken
skills is harder to debug than one that will not load at all; and the library
comes after the engine because `spec_lint.py` is the only practical way to
verify 150 archived changes ported correctly.

**Where this epic ends up.** The epic and its member artifacts are born in
shipd's library. Once the library port runs, they come across to shipd
rewritten — the record of how shipd was created, living in shipd.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| shipd-port-tool | `tools/port.py` in shipd: the ordered, boundary-aware token and path map, dry-run first, with unit tests over synthetic fixtures and an unanchored-match report | medium | low | medium | medium |
| shipd-engine-port | Port `plugins/s/` to `plugins/s/` with every namespace constant rewritten (`CONFIG_FILENAME`, `DEFAULT_DIR`, `DEFAULT_MEMORY_DIR`, build log dir, tui venv cache, worktree idle env var, semdiff cohort), all four test suites, `requirements.txt`, and shipd's `ci` workflow green | medium | high | medium | high |
| shipd-library-port | Port `.shipd/` to `.shipd/` — 34 verified capabilities with the sixteen `am-*` → `shipd-*` renames, 150 rewritten archived changes, epics, autopilot reports, research, video, `.shipd-config.json`; drop `.shipd/state.json` and `openspec/`; lint clean and metrics parity | low | high | medium | medium |
| shipd-identity | Marketplace manifest (`shipd` → `./plugins/s`), plugin manifest (`s`, one bump past shipd's then-current version), `.claude/settings.json` (`s@shipd`, statusline path), then register the marketplace, install the plugin, and confirm `/s:` skills load in a fresh session | low | high | medium | high |
| shipd-brand | README with new banner and `shipd.now`, `AGENTS.md`/`CLAUDE.md` restated for shipd, `.shipd/README.md` and `constitution.md`, the board's brand block, statusline header, tracked `docs/`, and replacing the throwaway README and Node-template `.gitignore` | low | low | low | low |
| shipd-evals-port | Port `evals/` — three case fixtures onto the `.shipd` layout, `run.py` driving `/s:plan` against the working-tree plugin, `evals/tests/` — and verify with a live run | low | medium | medium | low |
| shipd-selfhost | Close the local loop in shipd: plan → build → merge/archive one real change entirely under `/s:`, in a worktree cut by shipd's own `worktree.sh`, with shipd's own linter, status CLI, and merge engine | low | high | high | high |
| shipd-gated-merge | The remote half `shipd-selfhost` cannot reach: branch protection and the `ci` + `semantic-review` required checks on `shipd-now/shipd`, the six stacked member branches opened as PRs, and the exercise change auto-merged through the gate. Blocked on the credential question `q-shipd-pr-authoring` — no session can perform API writes against `shipd-now/shipd` today | low | high | high | high |
