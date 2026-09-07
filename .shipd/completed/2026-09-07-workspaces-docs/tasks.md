## 1. shipd binary — workspace modes, wiki, config

- [x] 1.1 [req: cli-dispatch] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, add tests (mirroring
      the existing board/render mode-word tests): `shipd workspace init
      --help` prints `workspace-init`'s usage and exits 0; `shipd workspace
      sync --help` prints `workspace-sync`'s usage and exits 0; `shipd
      workspace --help` still prints `workspace-show`'s usage; `shipd wiki
      init --help` prints `wiki-init`'s usage; `shipd wiki --help` prints
      `wiki-show`'s usage; `shipd config` from a repo root prints
      `config-show`'s `config (resolved from` header and exits 0; and the
      `shipd --help` banner lists `wiki` and `config`. Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests -p test_shipd_cli.py -v` and observe the
      new tests fail.
- [x] 1.2 [req: cli-dispatch] In `plugins/s/bin/shipd`: add `wiki` →
      (`spec_status.py`, `["wiki-show"]`) and `config` → (`spec_status.py`,
      `["config-show"]`) to `VERB_TABLE`; add mode-word handling for
      `workspace` (first trailing arg `init` → `workspace-init`, `sync` →
      `workspace-sync`, else fall through to `workspace-show` with args
      intact) and for `wiki` (`init` → `wiki-init`, else `wiki-show`),
      following the existing board/render mode-word implementation; update
      the usage banner (list `wiki` and `config`, and show
      `workspace [init|sync]`) and extend the module docstring's
      explicit-word exceptions sentence with the three user-domain writers
      (`workspace init`, `workspace sync --write-gitignore`, `wiki init`).
      Confirm the 1.1 tests now pass.

## 2. The workspaces guide

- [x] 2.1 [req: workspaces-doc] `git mv docs/portable-workspaces.md
      docs/workspaces.md`; retitle to `# Workspaces`; rewrite the intro to
      define a workspace (a git repo you clone to stand up a job to be done)
      without the phrase "portable workspace", and re-annotate the layout
      diagram so the top folder is labeled as the workspace repo.
- [x] 2.2 [req: workspaces-doc] In `docs/workspaces.md`, move every example
      to the `~/workspaces/<job>/` convention (running example
      `~/workspaces/documents-linking/`, members `documents/`, `tasks/`,
      `incentives/`) and replace the interactive commands: creation becomes
      `shipd workspace init ~/workspaces/documents-linking --git`, the
      bootstrap becomes `shipd wiki init` + `shipd workspace sync
      --write-gitignore`, day-to-day becomes `shipd workspace` /
      `shipd workspace sync`, and the store check in the external-store
      section becomes `shipd config`. No section outside §9 may invoke
      `spec_status.py` by path.
- [x] 2.3 [req: workspaces-doc] In `docs/workspaces.md`, rewrite the nesting
      section's example to file the nested job under its base workspace root
      (keeping `--nested --git` semantics and the inheritance/nearest-only
      lists unchanged), using `shipd workspace init <base-root>/<job>
      --nested --git`; keep §9 (headless consumers) on the raw
      `spec_status.py` footprint and add one sentence stating why — headless
      consumers run from a bare clone plus the plugin checkout, and that
      script footprint is the pinned contract.
- [x] 2.4 [req: workspaces-doc] Update the inbound references: the
      `[Portable workspaces](portable-workspaces.md)` link in
      `docs/oracle.md` becomes `[Workspaces](workspaces.md)`, and the
      `# portable-workspaces):` comment in
      `plugins/s/skills/build/scripts/spec_common.py` (sync-ladder comment,
      near line 1604) refers to `docs/workspaces.md` instead.

## 3. Ship

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version to
      `0.6.185`; run the full stdlib test suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      confirm it passes without `textual` installed; run `python3
      plugins/s/skills/build/scripts/spec_lint.py workspaces-docs` and
      confirm it is clean.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 82 | 19.0k |
| Write | 4 | 7.0k |
| (no tool) | 0 | 1.9k |
| Agent | 2 | 886 |
| Read | 12 | 882 |
| Edit | 10 | 396 |
| **Total** | 110 | 30.1k |
