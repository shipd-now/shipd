# dependency-check-store-base
Status: verified
Planned-at: c8cb8bb2446b8912c6bbc4376e254b1ac1645e09
Gated-hash: 584145e74d36

## Idea

Read an `After` dependency's merged state from the repository that tracks the
content directory, and report a git failure as an error.

### Motivation

Epic owners who keep specs in an external store cannot run dependent members:
each one parks as "not merged into origin/main" although the store's base
branch carries the completed entry. The predicate reads the code repository's
tree for a path outside it, and treats git's fatal error as "not merged".

### Details

- Resolve the repository from the content directory, not the invocation root.
- Resolve `origin/main`, else `main`, in that repository and list its
  `completed/` directory there.
- Raise an error on a git failure; keep "no base ref" as not merged.
- In the detached pre-build step: fetch the store's base, park a failed check
  with its cause, and name the store's repository in the waiting reason.
- Document the rule in the autopilot skill and the stores guide.

Affected capabilities: `epic-autopilot` (`member-wave-scheduling` modified,
`merged-dependency-check` added). Impact:
`plugins/s/skills/build/scripts/autopilot.py`,
`plugins/s/skills/build/tests/test_autopilot.py`,
`plugins/s/skills/autopilot/SKILL.md`,
`docs/workspaces/nesting-and-stores.md`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No change to `_sync_base_ref`, the worktree merge, or the drift measurement:
  they keep using the code repository's base.
- No change to `_build_grade`, which reads the on-disk `completed/` directory.
- No change to when the store is committed or pushed.
- No on-disk fallback for a store outside any git work tree.

## Implementation

All code edits land in `plugins/s/skills/build/scripts/autopilot.py`.

- **New helper `_dependency_base(command_fn, root, deps)` returns `(repo, ref)`.**
  `deps` is the dependency slug, or the member's `After` slugs joined with
  `, `; the error names it.
  It runs `git rev-parse --show-toplevel` with cwd `sc.specs_dir(root)`. A
  non-zero exit or blank output raises `AutopilotError` reading
  `dependency check for '<deps>' failed: content directory '<specs dir>' is
  not inside a git work tree (<first error line>)`. `repo` is the stripped output. `ref` is the first
  of `origin/main`, `main` (`ss.DEFAULT_AMEND_BASE`) that
  `git rev-parse --verify --quiet` resolves with cwd `repo`, else `None`.
  Rationale: `cmd_epic_amend_check` in `spec_status.py` anchors git the same
  way. Rejected: `git -C <root>` with a relative path, which is the bug.
- **`_merged_into_base(command_fn, root, slug, base=None)` keeps its name.**
  `base` is an optional `(repo, ref)` pair; when `None` the function calls
  `_dependency_base`. A `None` ref returns `False`. The listed path is
  `os.path.relpath(os.path.realpath(<specs dir>/completed),
  os.path.realpath(repo))`, `/`-separated with a trailing `/`; both sides are
  realpath'd because git prints a symlink-resolved top level. `git ls-tree
  --name-only <ref> -- <path>` runs with cwd `repo`. A non-zero exit raises
  `AutopilotError` reading `dependency check for '<slug>' failed in <repo>:
  <first error line, else "exit <rc>">`. The name-matching pattern is unchanged.
  Rewrite the docstring to state this rule.
- **`compute_waves` is not edited.** It calls the predicate without `base`;
  the `AutopilotError` propagates to `main`, which already prints
  `error: <message>` and exits 1.
- **New helper `_sync_store_ref(command_fn, root)`.** Where
  `sc.store_root_dir(root)` is not `None` and
  `sc.store_sync_enabled(sc.resolve_config(root)[0])` is true, it runs
  `git fetch origin main` with cwd `sc.specs_dir(root)` and ignores the exit
  code. Otherwise it runs nothing. Rationale: `store_sync` is the existing
  switch for networked git on the store.
- **`_pre_build_step` order:** `_sync_base_ref`, then `_sync_store_ref`, then
  one `_dependency_base` call whose pair is passed to every
  `_merged_into_base` call. An `AutopilotError` from either returns
  `("needs_human", "dependency", str(exc), None)` before any merge. The
  waiting reason keeps its wording with the dependency ref
  (`ref or ss.DEFAULT_AMEND_BASE`) in place of the code ref; where
  `sc.store_root_dir(root)` is not `None`, ` in the store repository <repo>`
  follows the ref.
- **Tests use the injectable `command_fn`, plus one real-git test.** The fakes
  `_FakeGit` and `_Seams.command_fn` answer `git rev-parse --show-toplevel`
  with `os.path.dirname(cwd)` unless told otherwise. One test builds two real
  repositories in a temp directory with `store_root` declared.

Risk: a root outside any git work tree used to count every dependency as
unmerged and now errors. This is the intended loud report; the suite's fakes
are updated so no existing test depends on the silent path. Risk: the store's
`origin/main` lags until the store is pushed; the stores guide states it.

## Readiness attestation

### Problem and motivation

Epic owners who keep specs in an external store cannot run dependent members:
every one parks as "not merged" although the store's base carries the
completed entry. The predicate reads the code repo's tree for a path outside
it.

Evidence:

- `plugins/s/skills/build/scripts/autopilot.py:702-729` runs `git ls-tree`
  from `root` on a path derived from `sc.specs_dir(root)`, and returns `False`
  on any non-zero exit.
- `plugins/s/skills/build/scripts/autopilot.py:1228-1233` parks the member
  with the reported `needs-human [dependency]` reason.
- The request states the expected rule: the entry on the base ref of the
  repository that tracks the spec store.

### Scope and non-goals

The change covers the dependency predicate, its pre-build caller, and the
error path. The code-repo base sync, merge, and drift measurement stay
untouched.

Evidence:

- In scope: `autopilot.py:702-729` and `autopilot.py:1225-1233`.
- Out of scope: `_sync_base_ref` at `autopilot.py:1123-1134`, which the
  request names as still correct; `_build_grade` at `autopilot.py:753-766`.
- Capability `epic-autopilot`, requirement `detached-pre-build-drift`, forbids
  the pre-build step from redefining the merged-dependency check.

### Affected capabilities and files

One capability and five files are affected: the driver, its tests, the
autopilot skill text, the stores guide, and the version file. The reproduction
ran and showed both the failure and the working store-anchored reads.

Evidence:

- Capability `epic-autopilot`: requirement `member-wave-scheduling` (base
  3d1d93645f8f, from `spec_status.py base-hash`); `merged-dependency-check`
  added.
- Files: `plugins/s/skills/build/scripts/autopilot.py:702`,
  `plugins/s/skills/build/tests/test_autopilot.py:203` and `:1306`,
  `plugins/s/skills/autopilot/SKILL.md:176`,
  `docs/workspaces/nesting-and-stores.md:200`,
  `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: in a scratch layout with `store_root` declared,
  `autopilot._merged_into_base(autopilot._run_command, <worktree>, "change-a")`
  returned `False` although the store's `main` tracks the entry.
- Runnable premise: `git -C <worktree> ls-tree --name-only main --
  ../../../specs/x/completed/` exited 128 with `is outside repository`.
- Runnable premise: `git -C <store>/code rev-parse --show-toplevel` exited 0
  and printed the store repository's root.
- Runnable premise: `git -C <store> ls-tree --name-only main --
  code/completed/` exited 0 and printed `code/completed/2026-01-01-change-a`;
  the same read on an absent path exited 0 with no output.
- Runnable premise: `git rev-parse --show-toplevel` outside any repository
  exited 128; `git fetch origin main` with no remote exited 128.
- Runnable premise: `python3 -B -m unittest tests.test_autopilot` ran 190
  tests and printed `OK` before the change.

### No open task-shaping decision

Repo selection, ref rule, and error handling come from the request. The store
fetch and the helper shape were settled by investigation; none remain.

Evidence:

- Which repository and ref to read: settled by the request.
- Git failure raises, missing ref blocks: settled by the request.
- Non-git store raises with no on-disk fallback: settled by investigation
  (the request's loud-report rule; `shipd-config` `store-autocommit` shows a
  non-git store has no base branch).
- Store fetch gated on `store_sync`: settled by investigation
  (`spec_common.py:624`).
- Error surface (waves exit 1, pre-build parks at `dependency`): settled by
  investigation (`autopilot.py:2145`, the `sync` parking at
  `autopilot.py:1235-1240`).
