# Tasks — workspace-consent

## 1. Engine — workspace-local clone sources

- [x] 1.1 [req: workspace-member-map, sync-materialization-planning] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add failing tests:
      the local map file's `clone_sources` key reads as a validated list
      (valid list, absent key → empty, `~` expansion, relative resolved
      against the workspace root, malformed value raises an error naming
      `.shipd-workspace.local.json`), and `plan_workspace_sync` scans the
      union of config and local sources (config entries first, duplicates
      removed after expansion; a local-only source yields a `worktree`
      candidate when config declares none). Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -v` and
      observe the new tests fail.
- [x] 1.2 [req: workspace-member-map] In
      `plugins/s/skills/build/scripts/spec_common.py`, extend the local map
      file loader (`REPO_MAP_FILENAME` readers near line 1853) with the
      optional `clone_sources` key: absent → empty list; a present value
      that is not an array of non-empty strings raises the loader's clear
      error naming the file; expose a reader returning the expanded,
      workspace-root-resolved directory list. Stdlib only.
- [x] 1.3 [req: sync-materialization-planning] In
      `plugins/s/skills/build/scripts/spec_common.py`, make
      `plan_workspace_sync`'s candidate scan draw on config `clone_sources`
      entries first, then the local file's, deduplicated after expansion.
      Confirm the 1.1 tests now pass.

## 2. Engine — workspace-sources verbs

- [x] 2.1 [req: workspace-sources-verbs] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add failing tests
      for `workspace-sources`: `add` creates the key while preserving
      `repos` and ensures the `.shipd-workspace.local.json` gitignore line
      outside the marked block; duplicate `add` exits zero without
      duplicating; `add` of a missing directory warns and writes; `remove`
      deletes exactly one entry and errors when none matches; the bare form
      lists stored values with resolved absolute paths; a malformed map
      file fails `add`/`remove` with the load's error. Run the suite and
      observe them fail.
- [x] 2.2 [req: workspace-sources-verbs] In
      `plugins/s/skills/build/scripts/spec_status.py`, add
      `cmd_workspace_sources` (list/add/remove) modeled on
      `cmd_workspace_map` (line 3608), wire it into the argparse verbs and
      the help text near the `workspace-map` entry (line ~130). Confirm the
      2.1 tests pass.

## 3. Workspace skill — the consent contract

- [x] 3.1 [req: workspace-clone-sync-flows] In
      `plugins/s/skills/workspace/SKILL.md`, rewrite the `sync` section
      (lines 236-300): after obtaining the plan, when any record carries an
      executable action, present one batched AskUserQuestion consent round —
      reuse existing checkouts where found and materialize the rest
      (recommended), materialize everything fresh, review member-by-member,
      or stop; include the checkout-folder question in the same round when
      no clone source resolves and an absent member lacks a candidate,
      persisting the answer via `workspace-sources add` and recomputing the
      plan before executing; reuse drives `workspace-map set` per candidate
      member and executes commands only for the rest; review falls into the
      map round's per-member shape; stop executes nothing; an all-`none`
      plan asks nothing. Keep the failure-continues, `--write-gitignore`
      reconcile, and roster-report steps.
- [x] 3.2 [req: workspace-setup-skill] In
      `plugins/s/skills/workspace/SKILL.md`, update the `clone` section to
      hand into the consenting sync flow (drop "No confirmation round — the
      invocation is the consent"), give `map` the same sourceless
      checkout-folder preflight (persist via `workspace-sources add`,
      re-read the plan before proposing), and rewrite "The question
      contract" section: `sync` and `clone` open exactly one up-front
      consent round and ask nothing further; `init` and `map` keep their
      single rounds.

## 4. Build skill — the materialization gate

- [x] 4.1 [req: workspace-member-materialization-gate] In
      `plugins/s/skills/build/SKILL.md`, add the workspace materialization
      gate to Phase 0 before the workflow gate: when the invocation
      resolves inside a discoverable workspace and the build target matches
      a declared member (per `workspace-show`) whose checkout is neither
      present nor mapped, read that member's record from
      `workspace-sync --json` and ask one AskUserQuestion — materialize
      (run the record's advisory `command:` exactly as printed), map an
      existing checkout (`workspace-map set` with the user's path), or
      stop — then continue the build from inside the resolved checkout;
      present-or-mapped targets and non-workspace invocations skip the gate
      silently.

## 5. Docs

- [x] 5.1 [req: workspaces-doc] Through the `/s:document` standard, update
      `docs/workspaces/member-map.md` (three local-file fields including
      `clone_sources`, the `workspace-sources` list/add/remove verbs) and
      `docs/workspaces/getting-started.md` (sync's single up-front consent
      question, reuse-where-found offered). Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py` over both
      pages until it exits 0.

## 6. Ship

- [x] 6.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` to
      `0.6.205`.
- [x] 6.2 [req: *] Verification barrier: run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -v`
      (all green, no `textual` installed) and
      `python3 plugins/s/skills/build/scripts/spec_lint.py workspace-consent`
      (exit 0).

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 114 | 37.8k |
| Edit | 38 | 29.3k |
| Read | 37 | 4.8k |
| Agent | 2 | 1.4k |
| (no tool) | 0 | 471 |
| Skill | 1 | 431 |
| Write | 1 | 411 |
| TaskStop | 1 | 23 |
| ToolSearch | 1 | 23 |
| **Total** | 195 | 74.7k |
