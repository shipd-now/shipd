# /s:workspace reference — the sync plan and its convergence rules

`workspace-sync --json` emits **one JSON record per line**. Each carries a
`kind`.

## `member` records

| field | meaning |
| --- | --- |
| `member` | the member's slug |
| `path` | where it materializes, relative to the workspace root |
| `state` | what is on disk now |
| `action` | `none`, `worktree`, `reference-clone`, `clone`, or `unmaterializable` |
| `source` / `url` / `branch` | where it comes from, as applicable |
| `command` | the advisory command to run **exactly as printed** |
| `drift` | an origin/manifest mismatch, or an occupied non-git path |
| `reason` | why an `unmaterializable` member cannot be created |

Act only on `action`:

- **`none`** — already a git work tree; touch nothing. Report any `drift:` note
  verbatim and never repair it.
- **`worktree`** — run the record's `command:` (local `git worktree add`).
- **`reference-clone`** / **`clone`** — run the record's `command:` (networked
  git, which only this command may run).
- **`unmaterializable`** — report the `reason:` and skip the member.

A member whose command exits non-zero is reported against that member; the run
continues with the rest.

## The trailing `gitignore` record

One record with `missing` and `stale` line lists. **Do not read the ignore
block's convergence from the same run that writes it**: the engine computes and
prints this record *before* `--write-gitignore` rewrites the block, so the very
invocation that fills the gaps still reports them. Treat the block as
reconciled by the write, or verify by reading the marked block in the workspace
root's `.gitignore` — it then lists exactly the manifest's member paths.

## Convergence

Confirm member convergence from the fresh `member` records of the
`--write-gitignore` run: each member you executed should read `action: none`
with no `drift:` note. Report any that did not.
