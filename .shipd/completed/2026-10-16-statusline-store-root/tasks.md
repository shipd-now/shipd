# Tasks — statusline-store-root

- [x] 1 [P1] [req: statusline-content-resolution, statusline-rendering, statusline-integration, statusline-chain] In `plugins/s/skills/build/tests/test_statusline.py`, add tests with a temp HOME and temp directory trees (fake `.git` directories and `.git` files, `.shipd-config.json` files, store folders) for every scenario in the change's statusline delta: relative `store_root`, registry path preferred over basename, linked worktree, renamed `dir`, missing store folder → `☕ no specs` with empty stderr, no content directory → `☕ no specs`, `--then 'echo theirs'` in a workspace with no content directory → `☕ no specs` then `theirs`, `--print-content-dir` output. Update existing tests that expected silence. Then implement the resolution, the `no specs` path, and `--print-content-dir` in `plugins/s/integrations/statusline.sh` per `plan.md` `## Implementation` (bash 3.2, no git/Python process), and update its header comment. The file passes.
- [x] 2 [P2] [req: doctor-verb] In `plugins/s/skills/build/tests/test_shipd_cli.py`, add doctor tests using temp trees and the real statusline script: a shipd registration where the engine's content directory exists and the script resolves the same → `ok`; a mismatch (stale in-repo `.shipd/` while `store_root` points elsewhere, or a store the script cannot match) → `warn statusline — ` naming both directories; a probe failure keeps the registration verdict. Then implement the comparison in `check_statusline` in `plugins/s/bin/shipd` per `plan.md`, threading `root` from `check_steps`. All of `test_shipd_cli.py` passes.
- [x] 3 [P2] [req: statusline-content-resolution] Revise the first "Known limitations" bullet in `docs/workspaces/nesting-and-stores.md` per `plan.md`, run `python3 plugins/s/skills/document/scripts/docs_lint.py docs/workspaces/nesting-and-stores.md` until it exits clean, and bump `version` in `plugins/s/.claude-plugin/plugin.json` one patch above the version the main branch carries at build time.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 33 | 2.8k |
| Agent | 2 | 840 |
| (no tool) | 0 | 401 |
| SubagentHandback | 2 | 52 |
| **Total** | 37 | 4.1k |
