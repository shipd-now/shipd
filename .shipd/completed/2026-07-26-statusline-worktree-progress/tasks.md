# Tasks — statusline-worktree-progress

## 1. Worktree-aware statusline

- [x] 1.1 [req: statusline-rendering] In `plugins/s/skills/build/tests/test_statusline.py`, add failing tests: an empty-root workspace with an `active` change under `.worktrees/w1/.shipd/planned/` renders that change's name/status/counts; two live specs render `(1 of 2)` after the name and `(13 of 20)`-style aggregate after the counts; an `active` worktree change beats a `ready` root selection; two `active` changes pick the newer `tasks.md` mtime; a workspace with `.shipd/` but no `planned/` dir prints `☕ no active specs`; a dir with no `.shipd/` prints nothing; several live specs with none pickable print `☕ <n> specs · none selected` counting worktree specs.
- [x] 1.2 [req: statusline-rendering] Implement in `plugins/s/integrations/statusline.sh`: candidate glob over `$ws/.shipd/planned/*/` and `$ws/.worktrees/*/.shipd/planned/*/`, the active-first pick with mtime tie-break (`stat -f %m` / `stat -c %Y` fallback), the `(1 of X)` and `(<t> of <Y>)` brackets when X > 1, and the `.shipd/`-gated silence semantics — bash 3.2, no runtimes. Tests from 1.1 pass.
- [x] 1.3 [req: statusline-rendering] Update the statusline blurb in `README.md` (rendered line format with the bracket forms) and bump `plugins/s/.claude-plugin/plugin.json` to the next patch version.
- [x] 1.4 [req: *] Verify: full unittest suite green; render the statusline manually against this repo (main checkout with the live worktrees) and confirm the active/bracket output matches the spec scenarios.
