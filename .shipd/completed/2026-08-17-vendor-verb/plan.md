# vendor-verb
Status: verified

## Idea

Add a `shipd vendor` verb that installs the plugin *into* a target repository —
a vendored, self-contained per-repo install alongside the existing global one.

### Motivation

shipd installs only at user scope today (`install.sh`, the cache launcher), so
a cloned repo is useless to a collaborator until they install shipd themselves.
Vendoring the plugin plus a self-advertising `.claude/settings.json` into the
repo — the pattern this repo already proves — makes a clone work after nothing
but the folder trust dialog.

### Details

- New curated `shipd vendor [add|remove] --root DIR` verb managing four
  surfaces in the target repo: the vendored plugin tree
  `<content-dir>/plugin/s/`, a generated
  `<content-dir>/plugin/.claude-plugin/marketplace.json`, merged keys in
  `.claude/settings.json`, and the minimal `<content-dir>/{verified,planned,
  completed}/` scaffold.
- Context-aware `pip install` hints in `shipd doctor`'s `pydantic`/`textual`
  checks — a vendored target repo has no `requirements.txt` to `-r` from.
- README documents the per-repo mode beside install mode and dev mode.

Affected capabilities: `shipd-cli` (modified `cli-dispatch`, `doctor-verb`;
added `vendor-verb`), `shipd-install` (modified `install-mode-docs`). Impact:
`plugins/s/bin/shipd`, `plugins/s/skills/build/tests/test_shipd_cli.py`,
`README.md`, `requirements.txt`, `plugins/s/.claude-plugin/plugin.json`
(version bump). No new dependencies.

### Non-goals

- No change to the global install path (`install.sh`, the `~/.local/bin/shipd`
  launcher, the GitHub marketplace flow).
- No shim generation for non-Claude-Code tools (Cursor etc.) — the vendored
  binary is directly runnable; that is the story for other tools.
- No automatic pip install of `pydantic`/`textual` — `/s:doctor` stays the
  consent-gated remedy path.
- No `.gitignore` edits and no commits in the target repo — the verb writes
  files; committing them is the owner's call.

## Implementation

- **Mirror the `copilot` verb contract** (`bin/shipd:636-830`): bare verb =
  read-only per-file state report exiting 0; `add` = idempotent atomic
  install/refresh refusing foreign files without `--force`; `remove` = guarded
  delete of owned files only. Rejected: a free-standing install script — the
  curated-verb pattern already carries state reporting, atomic writes, and
  ownership guards.
- **Vendor location: `<content-dir>/plugin/`** — `s/` holds the plugin copy,
  `.claude-plugin/marketplace.json` sits beside it so the directory is itself a
  marketplace root. The content dir is resolved through the engine's layered
  config (`resolve_config`, default `.shipd`), never hardcoded, so a repo with a
  custom `dir` key gets a matching settings pointer. Verified premise: a
  marketplace manifest validates from a subdirectory — `claude plugin
  marketplace add <tmp>/.shipd/plugin` succeeded (exit 0) against a probe
  layout. Rejected: mirroring this repo's root `plugins/s` +
  `.claude-plugin/` layout — claims two root names in the target repo for no
  gain.
- **Full byte-identical copy, tests included** (~5.7M). The recorded acceptance
  bar for a relocated engine is its suites running green in place, and the
  cache snapshot already ships the test suites; a stripped copy would be a
  second divergent layout. Drift = any vendored file differing from the running
  plugin's copy, or extraneous files; `add` prunes and rewrites to byte
  equality. Source tree is `PLUGIN_ROOT`, resolved relative to the binary, so
  checkout and cache snapshot behave alike.
- **Ownership marker**: the vendored `s/.claude-plugin/plugin.json` — owned
  when it parses with `"name": "s"`; its `version` against the running
  manifest version distinguishes `installed` from `stale`. A plugin dir whose
  manifest is missing, unparseable, or otherwise named is `foreign`. The
  generated marketplace.json (name `shipd`, one plugin `s`, source `./s`)
  is owned exactly when the adjacent `s/` tree is — mirroring how `semdiff.py`
  borrows the SKILL.md's ownership.
- **Settings merge**, via the `_read_settings`/`_write_settings` atomic
  pattern (`bin/shipd:532-560`) aimed at `<root>/.claude/settings.json`:
  set `enabledPlugins."s@shipd": true` and `extraKnownMarketplaces.shipd` =
  directory source at the resolved `<content-dir>/plugin` with
  `"autoUpdate": true` (declarative, idempotent); register the vendored
  statusline command **only when no `statusLine` key exists** — never replace
  an existing one, matching `statusline install`'s guard. `remove` deletes the
  two managed keys and a `statusLine` only when it points into the vendored
  tree.
- **Scaffold** `<content-dir>/{verified,planned,completed}/` with a `.gitkeep`
  each, creating only what is missing; `remove` never touches the scaffold or
  any spec content — that is the user's data.
- **Doctor hints go context-aware**: `check_pydantic`/`check_textual` keep the
  `pip install -r requirements.txt` hint when `<root>/requirements.txt`
  exists and otherwise print the pinned spec (`pip install 'pydantic>=2.12,<3'`
  / `'textual>=8.2.8,<9'`), mirroring the doctor skill's remedy table;
  `requirements.txt`'s mirror comment gains this third site. Risk: three
  mirror sites for the pins — guarded by the comment naming all three.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` to the next free
  patch version in the same PR, per the cache-snapshot rule (0.6.125 at build
  time — main took 0.6.124 while this change was in flight).
- Risk: a target repo's existing `shipd` marketplace registration at user
  scope shadows the vendored one on machines that installed globally — benign
  by precedent: this repo carries both and the user-scope install wins.

## Questions and answers

### Q1: Where does the vendored plugin live in a target repo?
- **Question:** Vendor under `.shipd/plugin/` (hidden, namespaced; subdir
  manifest verified) or mirror the shipd repo's own root layout
  (`plugins/s/` + root `.claude-plugin/marketplace.json`)? Recommendation:
  `.shipd/plugin/`.
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** `.shipd/plugin/` — shipd's durable convention is a single
  namespaced footprint in a consumer repo; the shipd repo's root layout exists
  because that repo is the marketplace source, not as a consumer-side model.
  Derive the settings pointer from the resolved content dir rather than the
  literal `.shipd`, since the `dir` key is configurable.
- **Cited:** verified/shipd-config, epic/shipd-dx

### Q2: Full plugin copy or exclude the test suites?
- **Question:** Copy the whole plugin byte-identically (5.7M incl. 2.9M tests)
  or exclude `tests/`, `tests_textual/`, `tests_pydantic/` (~2.7M)?
  Recommendation: exclude.
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Full copy, tests included — overriding the recommendation. The
  recorded acceptance bar for a relocated engine is green suites at the
  destination; the cache snapshot already ships the suites in full, and a
  stripped vendored copy would be a second divergent layout of the same
  artifact for a negligible disk saving.
- **Cited:** epic/shipd-port, verified/shipd-port, verified/shipd-cli

### Q3: What is the verb called?
- **Question:** `shipd vendor [add|remove]`, `shipd repo [add|remove]`, or
  `shipd install`? Recommendation: `shipd vendor`.
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** `shipd vendor [add|remove]`, targeting via `--root DIR` like
  `copilot`. `install` is disqualified — the `shipd-install` capability
  already owns "install shipd itself", so `shipd install` would misread; and
  `repo` names a scope, not an operation.
- **Cited:** verified/shipd-cli, verified/shipd-install
