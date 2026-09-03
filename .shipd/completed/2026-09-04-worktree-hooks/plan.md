# worktree-hooks
Status: verified

## Idea

Make worktree creation an engine operation — a `shipd worktree` verb backed by
a new `worktree.py` script that drives the git mechanics and then runs the
repo's configured `post-worktree-scripts` in order — and add an
`s:worktree-hooks` skill that authors those setup scripts into the checked-in
content directory and registers them through the binary.

### Motivation

A fresh worktree often needs repo-specific setup — a `.env` copied in, a
database seeded — and today nothing runs after `git worktree add`
(`worktree.sh` ends at its "Next steps" prose), so every session repeats that
setup by hand or forgets it. There is no configurable hook point and no
programmatic front door: each skill shells the bash helper directly.

### Details

- New config key `post-worktree-scripts` in `.shipd-config.json`: an ordered
  JSON list of shell command lines, resolved through the existing layered
  merge.
- New stdlib-only engine script
  `plugins/s/skills/build/scripts/worktree.py`: create path (wrapping
  `worktree.sh`'s git mechanics, then running the hooks), `remove` /
  `prune-branches` passthrough, and a `hooks` verb family
  (`list`/`add`/`remove`/`run`) so config edits are engine-mediated.
- The `shipd` binary gains a curated `worktree` verb delegating to
  `worktree.py`; `autopilot.py` and every skill that creates a worktree switch
  to that path.
- New `s:worktree-hooks` skill: authors a setup script into
  `<content-dir>/hooks/`, registers it via `shipd worktree hooks add`, and can
  list/remove registered hooks.

Affected capabilities: `shipd-config` (added key requirement), `shipd-cli`
(modified dispatch), `build-spec-lifecycle` (modified worktree-isolation),
new `worktree-hooks` and `shipd-worktree-hooks`. Impact:
`plugins/s/skills/build/scripts/worktree.py` (new), `plugins/s/bin/shipd`,
`plugins/s/skills/build/scripts/autopilot.py`,
`plugins/s/skills/worktree-hooks/SKILL.md` (new),
`plugins/s/harness/bodies/worktree-hooks.md` (new), skill docs naming the
create path, `AGENTS.md`, plugin version bump.

### Non-goals

- `remove` and `prune-branches` stay implemented in `worktree.sh`; the Python
  layer only passes them through — no port of the guarded teardown.
- No pre-worktree or post-remove hooks; only the post-create step.
- No `shipd doctor` check for hook health, and no pipeline stage.

## Implementation

- **`worktree.py` dispatch mirrors `worktree.sh`.** First argument `remove`,
  `prune-branches`, or `hooks` selects that verb; any other first argument is
  a change name for the create path (with optional `--fresh` passed through).
  `remove`/`prune-branches` re-exec `worktree.sh` with the arguments verbatim
  (subprocess, exit code passed through). Rejected: porting the whole bash
  helper to Python — its create/adopt/guard behavior is battle-tested and the
  hook point only needs to wrap it.
- **Create path.** Resolve and validate `post-worktree-scripts` via
  `spec_common.resolve_config` *before* any git mutation, so a malformed key
  never leaves a half-set-up worktree. Record whether `.worktrees/<name>`
  already exists, run `worktree.sh <name> [--fresh]` with `cwd` = the repo
  root and stdout/stderr inherited, and on exit 0 run the hooks only when the
  worktree did not pre-exist (fresh create or branch attach). A reused
  worktree was already set up — hooks are skipped; `hooks run` covers manual
  re-runs.
- **Hook execution semantics.** Each list item is a shell command line run via
  `subprocess.run(item, shell=True)` with `cwd` = the new worktree, the parent
  environment plus `SHIPD_WORKTREE` (absolute worktree path), `SHIPD_ROOT`
  (repo root), and `SHIPD_CHANGE` (the name). Announce each item
  (`post-worktree: running <item>`) before running it. The first non-zero
  exit stops the chain and exits `3` — distinct from `worktree.sh`'s `1`
  (usage/error) and `2` (guard refusal) — with the worktree left in place.
  Command lines subsume script paths, so a checked-in script registers as its
  repo-relative path. Runnable premise: `worktree.sh worktree-hooks` observed
  exiting 0 with "Created worktree"; `shipd worktree` observed exiting 2
  (unknown verb) before this change.
- **`hooks` verbs.** `hooks list [--json]` prints the effective resolved list
  with each item's index and the declaring config path (provenance);
  `hooks add <item>` appends to `<root>/.shipd-config.json`, creating the file
  or key as needed, refusing an exact duplicate, and warning when a nearer
  declaration now shadows an outer layer's list; `hooks remove <item|index>`
  deletes one entry from the root file's list; `hooks run` executes the
  effective list with `cwd` = the invocation root (for re-running setup inside
  an existing worktree); with no change name in hand its env resolves as
  `SHIPD_WORKTREE` = the invocation root, `SHIPD_CHANGE` = its basename, and
  `SHIPD_ROOT` = the main checkout via `git rev-parse --git-common-dir`,
  falling back to the root when git cannot answer. Writes preserve unrelated
  keys and emit 2-space
  indented JSON with a trailing newline, matching the existing file style.
- **Config key contract.** `post-worktree-scripts` is a JSON list of non-empty
  strings, merged nearest-wins-wholesale like every top-level key. A declared
  value of any other shape errors naming the key.
- **Binary and call-site switch.** `bin/shipd` adds `worktree` to the curated
  verbs, delegating via `os.execv` to `python3 worktree.py` with trailing
  arguments verbatim, and lists it in the usage banner. `autopilot.py`
  replaces its create invocation `[WORKTREE_SH, slug]` with
  `[sys.executable, WORKTREE_PY, slug]`; its stale-reclaim `remove` stays on
  `worktree.sh`. Skill docs (build, plan, epic, research, autopilot,
  initiative — SKILL.md and matching harness bodies) and `AGENTS.md` switch
  worktree *creation* invocations to
  `"${CLAUDE_PLUGIN_ROOT}/bin/shipd" worktree <name>`; `remove` and
  `prune-branches` references are unchanged.
- **Skill.** `s:worktree-hooks` writes the authored setup script to
  `<content-dir>/hooks/<slug>.sh` (repo-local, resolved from the `dir` key;
  deliberately not relocated by `store_root`, because hooks must be checked in
  to travel with every worktree checkout), marks it executable, registers the
  repo-relative path through `shipd worktree hooks add`, and verifies with
  `hooks list`. Removal flows confirm with the user before
  `hooks remove`. The skill resolves the binary like `s:doctor`: `shipd` on
  PATH, else `${CLAUDE_PLUGIN_ROOT}/bin/shipd`.
- **Rejected: git's native `post-checkout` hook.** Git runs `post-checkout`
  after `git worktree add` (null-ref first parameter, flag `1`, cwd = the new
  worktree), but hooks live in `.git/hooks/` per clone — a checked-in hooks
  directory needs a per-machine `core.hooksPath` bootstrap, which is the very
  setup gap this change closes. The hook also fires on every checkout/switch/
  clone and its exit code cannot fail the operation, so a broken setup script
  is silent, where the engine path exits `3` and autopilot can park the
  member. Decision settled with the user (option 1a): engine mechanism,
  git-hook alternative rejected.
- **Risk: hooks run arbitrary shell from repo config.** Accepted — the config
  and scripts are checked in and code-reviewed like any other repo content,
  and the announce-before-run line keeps execution attributable. Risk: a
  failing hook mid-list leaves partial setup; guarded by the distinct exit `3`,
  the kept worktree, and `hooks run` for resume-by-rerun.
