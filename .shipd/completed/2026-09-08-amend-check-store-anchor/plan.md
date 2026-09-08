# amend-check-store-anchor
Status: verified

## Idea

Anchor `epic-amend-check`'s git lookups on the repository tracking the epic
and give the epic amend flow a store-aware shipping path, so live-epic
amendments work when `store_root` relocates the content directory into an
external repository.

### Motivation

Under a declared `store_root` the epic file lives in a different git
repository than the consuming repo, but `cmd_epic_amend_check` anchors
`rev-parse --show-toplevel`, `merge-base`, and `show` on the invocation root,
so the derived relpath escapes that repo's toplevel and the verb fails with a
misleading "epic does not exist at the base" error. The amend flow's
worktree/branch/PR ceremony likewise assumes the epic is tracked in the
consuming repo, leaving store-resident epics unamendable.

### Details

- Anchor the three git calls in `cmd_epic_amend_check` on the directory
  holding the epic file, and fix the docstring and the not-a-work-tree error
  message accordingly.
- Branch the `/s:epic <slug> amend` flow in `plugins/s/skills/epic/SKILL.md`:
  under a store there is no worktree, branch, or PR — the flow gates the
  uncommitted store edit, then makes one scoped local commit in the store
  repository, never pushed.
- Regression tests for the store-backed case in
  `plugins/s/skills/build/tests/test_spec_status.py`.

Affected capabilities: `spec-status` (modified), `shipd-epic` (modified).
Impact: `plugins/s/skills/build/scripts/spec_status.py`,
`plugins/s/skills/epic/SKILL.md`,
`plugins/s/skills/build/tests/test_spec_status.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump).

### Non-goals

- No change to `repo_store_folder`'s basename derivation: `--root` keeps
  naming the consuming repo (the documented `store-repo-folder-name` design);
  the flow documents that rather than adding a store-addressing CLI surface.
- No change to the `store-autocommit` engine requirement or `spec_common` —
  the amend commit is the skill's job, mirroring that convention.
- No PR or review workflow for the store repository.

## Implementation

- **Anchor on the epic's directory, not the root**
  (`spec_status.py`, `cmd_epic_amend_check`): set
  `anchor = os.path.dirname(path)` and run `rev-parse --show-toplevel`,
  `merge-base HEAD <base>`, and `show <sha>:<relpath>` through
  `_git_capture(anchor, ...)`; derive `relpath` from the realpath'd epic path
  against the realpath'd toplevel exactly as today. In the no-store case the
  anchor sits inside `root`'s repo, so behavior is unchanged — the existing
  amend-check tests must keep passing untouched. Verified by running: anchored
  on the consuming root the lookup fails (relpath `../store-repo/...`,
  exit 1); anchored on the epic's directory,
  `git -C <epic-dir> show <merge-base>:specs/consumer/epics/e1/epic.md`
  succeeds.
- **Docstring and error text follow the anchor**: the docstring's "works
  identically from the main checkout and from a linked amendment worktree"
  claim becomes "from the repository tracking the epic — the consuming repo
  in the default in-repo case, the external store's repository under
  `store_root`"; the not-a-work-tree error names the epic's directory, not
  `root`.
- **Store-aware amend flow** (`skills/epic/SKILL.md`, amend mode): detect the
  store case by running `spec_status.py --root <repo-root> config-show` and
  checking for a `store:` line (printed exactly when `store_root` is
  declared). When present: skip the amendment worktree entirely; edit the
  epic in place in the store's working tree; run both gates against the
  **uncommitted** edit with `--root <repo-root>` still naming the consuming
  repo; then ship as one local commit in the store repository scoped to the
  epic file, subject `shipd: amend epic <slug>` (matching `spec_merge.py`'s
  `shipd: merge change <slug>` convention), never pushing; report the commit
  hash instead of a PR URL. Rejected: branch + PR in the store repo — it
  contradicts the verified `store-autocommit` local-commit-never-push
  convention and would flip the shared store working tree onto a branch
  visible to every consuming repo.
- **Gate ordering is the protection**: the gates run before the commit. On a
  store checkout sitting on `main`, `merge-base HEAD main` is `HEAD`
  (verified by running), so gating the uncommitted edit compares it against
  the last committed state — the accretion check — never a vacuous pass. The
  flow's existing rule that a non-4 non-zero gate exit stops the amendment
  covers the non-git store, where the verb errors because there is nothing to
  compare against.
- **Tests** extend the existing amend-check fixture class
  (`test_spec_status.py`, `epic-amend-check` suite): a store fixture builds a
  consumer repo plus a separate store git repo, writes the consumer's
  `.shipd-config.json` with an absolute `store_root`, and commits the epic in
  the store. Covered: a clean amendable uncommitted store edit exits 0; a
  protected uncommitted store edit exits 4 with its finding line; a store
  outside any git work tree exits non-zero, not 4, with an error naming the
  epic's directory. Stdlib-only, local git only, per the constitution.

Risk: `_STORE_FOLDER_CACHE` memoizes per process, but the suite invokes the
CLI as a subprocess per call, so no cross-test bleed.

## Questions and answers

### Q1: How does a store-resident epic amendment ship?
- **Question:** When `store_root` places the epic in an external git-backed
  store, how should `/s:epic <slug> amend` ship the amendment? Options:
  (a) mirror the store's auto-commit convention — gate the uncommitted edit,
  then one local commit in the store scoped to the epic file, never pushed,
  with no branch or PR; (b) create a branch and pull request in the
  repository tracking the store. Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option (a). The verified library binds engine writes into an
  externally resolved store to exactly the local-commit-never-push
  discipline, scoped to the written paths, and reserves the branch/PR
  workflow for in-repo artifacts; option (b) contradicts that standing
  convention. The PR discipline stays in the consuming repo where the flow
  already runs its gates; the store side gets the scoped local commit.
- **Cited:** verified/shipd-config, verified/shipd-wiki
