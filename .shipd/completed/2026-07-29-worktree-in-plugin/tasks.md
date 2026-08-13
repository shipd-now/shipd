# Tasks — worktree-in-plugin

## 1. The plugin helper

- [x] 1.1 [req: plugin-worktree-helper] Add `plugins/s/skills/build/tests/test_worktree.py` with failing subprocess tests mirroring `test_claim_task.py`'s fixture style: in a temp git repo (init + one commit), the plugin helper creates `.worktrees/my-change` on branch `change/my-change` and exits 0 with the worktree path in its output; an existing `change/my-change` branch is refused non-zero with no worktree created; running in a dir with no `.git` errors non-zero naming the repo-root requirement; a second different change name succeeds alongside the first.
- [x] 1.2 [req: plugin-worktree-helper] Add `plugins/s/skills/build/scripts/worktree.sh` — port the logic from `scripts/worktree.sh` verbatim (worktree add, branch naming, refusal, `.worktrees/` creation) with repo-neutral next-steps text; keep it plain bash and `bash -n`-clean. Tests from 1.1 pass.

## 2. Repoint and remove

- [x] 2.1 [req: change-worktree-isolation] Repoint every live reference from `scripts/worktree.sh` to the plugin path: `plugins/s/skills/plan/SKILL.md`, `plugins/s/skills/build/SKILL.md` (both the workflow gate and the epic-close-out section), `plugins/s/skills/epic/SKILL.md`, `plugins/s/skills/initiative/SKILL.md`, `AGENTS.md`'s workflow section, and the `bash -n` line in `.github/workflows/ci.yml`; then `git rm scripts/worktree.sh` (and the now-empty `scripts/` dir if nothing else remains).
- [x] 2.2 [req: plugin-worktree-helper] Bump `plugins/s/.claude-plugin/plugin.json` one patch version.

## 3. Verification

- [x] 3.1 [req: *] Full barrier: unittest suite green; library lint clean; `bash -n plugins/s/skills/build/scripts/worktree.sh` passes; a repo-wide grep shows no live `scripts/worktree.sh` reference outside `.shipd/completed/` and `openspec/`; live drive — in a scratch git repo, run the plugin helper to create a worktree, confirm branch and refusal behavior, then remove the scratch repo.
