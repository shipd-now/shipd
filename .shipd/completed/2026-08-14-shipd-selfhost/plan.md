# shipd-selfhost
Status: verified
Epic: shipd-port
Theme: spec-engine

## Idea

Close the loop: plan, build, merge, and archive one real change entirely with
shipd's own skills and engine scripts, under `/s:`, with no shipd involvement.

### Motivation

Every earlier member proves a part in isolation — the engine's tests pass, the
library lints, the plugin loads — but none proves the whole cycle works in shipd.
Until a change goes plan → build → merge/archive there, driven by shipd's own
worktree script, linter, and merge engine, the port is a copy rather than a
working system.

### Details

- Run one real, small change through the full `/s:` lifecycle in shipd, in a
  worktree created by shipd's own `worktree.sh`.
- Confirm the archive, the master library, and the epic status all updated as the
  engine intends.
- Confirm no command in the lifecycle resolved to an shipd path or an `/s:`
  skill.

Affected capabilities: `shipd-port` (added). Impact: one change's worth of
artifacts and code in the shipd repository.

### Non-goals

- **No remote gate work.** Branch protection, the required-check configuration,
  PR creation, the `semantic-review` status post, and auto-merge on
  `shipd-now/shipd` are all out of scope here — see the Implementation note
  below. They move to the successor member `shipd-gated-merge`.
- No migration of shipd's open work. In-flight shipd changes finish in
  shipd.
- No decommissioning of shipd. It stays installed and working; the epic's
  central constraint is that both exist afterward.
- No large feature. The change run through the loop is deliberately small — its
  purpose is to exercise the pipeline, not to deliver scope.
- No autopilot run. Proving the unattended pipeline is separate work; this member
  proves the interactive one.

## Implementation

- **The remote half of this member is deferred, not skipped, because it is
  physically unreachable from a session.** `shipd-now/shipd` is private;
  `gh` on this machine authenticates only as `mikkel-bergmann` and gets a 404 on
  the repo; no PAT, `GH_TOKEN`, `.netrc`, or keychain entry exists; and the
  `shipd-syncd` GitHub App has a single installation, on the `mikkel-bergmann`
  account rather than `shipd-now`. The `github-shipd` SSH alias authenticates as
  `shipd-now` but grants git ref writes only. Branch protection, PR creation,
  commit statuses, and auto-merge are API-only operations, so no session can
  perform them until the credential question — the workspace queue's pending
  `q-shipd-pr-authoring` — is answered. That work is filed as the successor
  member `shipd-gated-merge` rather than carried here as requirements this
  change cannot meet.

- **The unmet requirements are not merged.** `spec_merge.py` promotes a delta's
  ADDED requirements into `verified/`, the library of what *is true* of the
  system, and the constitution makes completed changes immutable. Merging a
  branch-protection requirement while shipd's default branch has no protection
  would write a false assertion into shipd's master library on the first day of
  its self-hosting life, retractable only by a further change carrying a REMOVED
  requirement. So this member's delta carries only the lifecycle requirement it
  actually satisfies.

- **The exercise change is chosen for coverage, not size.** It must touch
  `plugins/s/` so it exercises the plugin-version bump, and it must carry a delta
  spec so `spec_merge.py` has something real to merge into the master library and
  archive. A docs-only change would skip both and prove less. A small engine
  change with a matching test satisfies both and stays reviewable.

- **The exercise worktree branches off the six-branch stack, not `main`.**
  shipd's `main` is still the initial commit — no `plugins/s/`, no `.shipd/`, no
  `ci.yml` — because the six prior member branches are pushed but not yet merged
  (they cannot be, for the same credential reason). A worktree cut from `main`
  would have no `/s:` engine to self-host with, so the exercise stacks on
  `change/shipd-evals-port`, the tip of the stack. This keeps the stack
  reviewable for whoever opens the PRs.

- **Epic derivation is the last thing checked.** The shipd library carries the
  `shipd-port` epic (ported in member 3) whose status will have been frozen at
  the pinned ref. Re-deriving it in shipd with the ported status CLI is both the
  final correctness check and the act that leaves shipd's library self-consistent.

- **Success is defined by artifacts on disk, not by the session's report.** The
  member is done when shipd's exercise branch carries the merged change, its
  master library carries the merged requirement, and its archive carries the
  dated completed directory. A session claiming success without those is a
  failure.

Risk: stacking the exercise change on `change/shipd-evals-port` means it inherits
that stack's review burden — if an earlier branch is revised before its PR opens,
the exercise change rebases with it. Accepted: the alternative (branching off an
empty `main`) cannot run shipd's engine at all.
