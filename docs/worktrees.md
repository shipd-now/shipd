<!-- doc-type: how-to -->

# Worktrees and hooks

shipd builds every change in its own git worktree. One change lives in one
worktree at `.worktrees/<change>`, on branch `change/<change>`, and ships as
one pull request. The `shipd worktree` verb family creates, removes, and
reclaims those worktrees.

A fresh worktree often needs repo-specific setup: a `.env` copied in, a
database seeded, dependencies installed. Hooks are the setup scripts the
create path runs right after it creates a worktree. `/s:worktree-hooks`
authors and registers them for you.

## When to use it

- **Start a change.** Create its worktree, then run the whole lifecycle —
  `/s:plan`, `/s:build`, merge and archive — inside it.
- **Set up every new worktree the same way.** Register a hook once, and every
  later create runs it.
- **Clean up after a merge.** Remove the merged worktree, and reclaim the
  local branches whose content already landed.

The main checkout serves only to launch sessions, review, and pull after a
merge.

## How to run it

### Create a worktree

1. Run the create path from the repository root:

   ```
   shipd worktree <change>
   ```

2. Pass `--fresh` to never adopt an existing worktree or unmerged branch:

   ```
   shipd worktree <change> --fresh
   ```

The change name must be kebab-case. A reused worktree skips its hooks,
because they ran when the create path first built it. After every create,
the engine also runs `sweep` unless the config disables it.

### Register a setup hook

1. Run `/s:worktree-hooks` and describe the setup step. The skill authors the
   script under `<content-dir>/hooks/`, registers it, and lists it back.
2. Or register a command line or a repo-relative script path yourself:

   ```
   shipd worktree hooks add "npm install"
   shipd worktree hooks add ".shipd/hooks/copy-env.sh"
   ```

3. Commit the script and `.shipd-config.json`, so every clone runs the hook.

Never hand-edit `.shipd-config.json` to register a hook. The `hooks add` and
`hooks remove` verbs own the format, the duplicate refusal, and the shadowing
warning.

A hook runs with the new worktree as its working directory. It reads
`SHIPD_WORKTREE`, `SHIPD_ROOT`, and `SHIPD_CHANGE` from the environment.

### Recover from a failing hook

The create path stops at the first hook that exits non-zero, and exits `3`.
It leaves the worktree in place.

1. Fix the failing script.
2. From inside the worktree, re-run the whole list:

   ```
   shipd worktree hooks run
   ```

A list this machine has not trusted also exits `3`. A terminal prompts for
consent; a session without a terminal refuses. Run `shipd worktree hooks
trust` to record consent without running the list.

### Clean up after a merge

1. From the main checkout, remove the worktree through the guarded verb:

   ```
   shipd worktree remove <change>
   ```

2. Reclaim merged local branches, squash merges included:

   ```
   shipd worktree prune-branches
   ```

`remove` refuses with exit `2` while the worktree still shows work in
progress. Pass `--force` only once you confirm the refusal is spurious.

## Reference

### Verbs

| Verb | Effect |
| --- | --- |
| `shipd worktree <change> [--fresh]` | Creates `.worktrees/<change>` on `change/<change>`, then runs the hooks. |
| `remove <change> [--force]` | Removes one worktree, refusing while it shows work in progress. |
| `prune-branches` | Deletes local `change/*` branches already merged, and lists the ones it keeps. |
| `sweep [--dry-run]` | Runs `remove` and `prune-branches` across every worktree, and reports an unmerged one on a `stale:` line. |
| `hooks list [--json]` | Lists each registered hook with its index and declaring config file. |
| `hooks add <item>` | Registers one command line or script path. |
| `hooks remove <item-or-index>` | Removes one registered hook. |
| `hooks run` | Re-runs the registered list inside an existing worktree. |
| `hooks trust` | Records this machine's consent to the list without running it. |

Every verb except `remove`, `prune-branches`, and `sweep` accepts
`--root DIR`, which names the repository root to act on.

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success. |
| `1` | Usage error or other error. |
| `2` | A guard refusal, such as `remove` on a worktree in use. |
| `3` | A hook failed, or its consent gate refused. |

### Config keys

The `post-worktree-scripts`, `worktree_sweep`, `worktree_idle_minutes`, and
`worktree_stale_days` keys tune this verb family; see
[Customising shipd](customise.md).

### Related pages

- [Build a change](build.md) — the lifecycle that runs inside a worktree.
