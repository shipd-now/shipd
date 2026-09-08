# coordinator-store-paths
Status: verified

## Idea

Resolve the task coordinator's and the worktree remove guard's content paths
through the engine, so both work when `store_root` relocates the content
directory into an external store — and when a repo merely renames its
content directory.

### Motivation

`claim_task.sh` hardcodes `.shipd/planned/<change>/` with no config
resolution, so under a declared `store_root` (or a renamed `dir`) every
coordinator verb dies with `tasks file not found` — taking out the whole
execution loop every build sub-agent depends on. `worktree.sh remove`
resolves only the `content-dir:` line, so under a store its unshipped-change
and task-claim guards scan an empty in-worktree path and go vacuous.

### Details

- `claim_task.sh` resolves its base directory through `config-show`:
  the `store:` line when present, else the `content-dir:` line, else the
  literal `.shipd`.
- `worktree.sh`'s remove guard additionally parses the `store:` line from
  its existing `config-show` call and, where a store resolves, checks the
  store's `planned/<change>` for the change under removal.
- Regression tests for both scripts' store and renamed-dir cases.

Affected capabilities: `build-task-coordination` (modified),
`build-spec-lifecycle` (modified). Impact:
`plugins/s/skills/build/scripts/claim_task.sh`,
`plugins/s/skills/build/scripts/worktree.sh`,
`plugins/s/skills/build/tests/test_claim_task.py`,
`plugins/s/skills/build/tests/test_worktree.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump).

### Non-goals

- No change to the store's write discipline: local-commit-never-push stands
  per the verified `store-autocommit` and store-resident-amendment
  requirements (oracle-settled this session); a branch/PR redesign would be
  a deliberate spec change proposed separately.
- No edits to `design.py`, `build_report.py`, `install_tui.py`, or
  `worktree.py` — audited; they touch only user-home scratch/log roots or
  root-level config files, which are correct under a store.
- No engine (Python) path changes — `specs_dir` already resolves stores;
  only the two shell surfaces lag.

## Implementation

- **`claim_task.sh` base resolution** (replacing the literals at lines
  139-141): add `SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)`
  (mirroring `worktree.sh:52`), run
  `python3 "$SCRIPT_DIR/spec_status.py" config-show 2>/dev/null` **once**,
  capture its output, and parse both lines:
  `store: ` via `sed -n 's/^store: //p' | head -n 1` and `content-dir: `
  likewise. Precedence: a non-empty store wins (verified by running — under a
  store `config-show` prints *both* lines, and `store:` carries the fully
  resolved per-repo content directory, e.g.
  `<store root>/specs/<repo folder>`); else the content dir; else the
  literal `.shipd` when the invocation fails or prints nothing (python3
  absent, malformed config) — resolution failure degrades to exactly
  today's behavior, never less. Then
  `TASKS="$BASE/planned/${CHANGE}/tasks.md"` and likewise `LOCK`/`CLAIMS`.
  No `--root` flag: the script's contract is run-from-project-root, so cwd
  resolution matches the engine's. One `config-show` per invocation is
  acceptable on the claim hot path — `worktree.sh` already pays it.
- **`worktree.sh` guard extension** (the guard block at lines 220-265):
  capture the existing `config-show --root "$WORKTREE"` output once and
  parse `store:` beside the current `content-dir:`. Where the store line is
  non-empty, guards 2 and 3 additionally check
  `"$store/planned/$CHANGE"` — **scoped to the change being removed**, whose
  name the `remove <change>` verb already receives: an existing directory
  adds an unshipped-change reason naming the store path; a `- [~]` mark in
  its `tasks.md` adds the claim reason; a `.tasks.lock` beside it adds the
  lock reason. The base-content carve-out (`planned_is_base_content`) does
  not apply to store paths — a change in the store's `planned/` is in-flight
  by definition. Rejected: scanning the whole store `planned/` — the store
  is shared by every worktree of the repo, so that would block removing any
  worktree while any change is in flight. The in-worktree scan stays exactly
  as it is, so in-repo behavior is unchanged.
- **Tests** extend the existing suites (both drive the real scripts as
  subprocesses): in `test_claim_task.py`, a store fixture (consumer git repo
  plus external store directory, `.shipd-config.json` declaring an absolute
  `store_root`, tasks file under `<store>/<repo folder>/planned/<change>/`)
  proving `status`/`claim`/`complete` operate on the store's tasks file, and
  a renamed-dir fixture (`dir` key) proving the `content-dir:` leg; in
  `test_worktree.py`, guard cases — an unshipped change in the store's
  `planned/<change>` refuses removal (exit 2, reason naming the store path),
  a `- [~]`/`.tasks.lock` there refuses, an unrelated store change does
  *not* block, and a clean store lets removal proceed. Local git only, no
  network, per the constitution.

Risk: `config-show` output grammar is the coupling seam — both scripts parse
its `store:`/`content-dir:` lines, which `cmd_config_show` prints from the
same `specs_dir`/`store_root_dir` funnel every engine verb uses, so drift
would require changing that verb's printed contract, which is itself
spec-bound.

## Questions and answers

### Q1: Should the store's write discipline gain branches/PRs?
- **Question:** The engine writes autonomously to the store repo's `main`
  (install/gate auto-commits, the amend flow's scoped commit); a user-side
  agent argues for branch/PR discipline in the store repository. Options:
  (a) keep the local-commit-never-push convention; (b) redesign store writes
  around branches/PRs. Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Keep the local-commit-never-push convention. The store's write
  discipline is a deliberate, verified design — every engine write into a
  git-backed store lands as one local commit scoped to the written paths,
  the engine never pushes, and the amend flow explicitly refuses to create a
  branch or PR in the store repository. A branch/PR redesign would
  contradict two verified requirements, so it is a spec change to propose
  deliberately, not a drift to fix.
- **Cited:** verified/shipd-config, verified/shipd-epic
