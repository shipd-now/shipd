# merge-safety-hardening
Status: verified

## Idea

Stop an armed auto-merge PR from waiting forever when it becomes un-mergeable:
make the build verify mergeability after arming, watch its own PR to a terminal
state, wait for its own merge before closing out, and have the autopilot refuse
to call an un-merged member `shipped`.

### Motivation

`gh pr merge --auto` is fire-and-forget today (`build-spec-lifecycle/ship-changes-as-prs`)
and `drive_member` records `outcome="shipped"` even when the PR never merged
(`autopilot.py:615`) — so a PR that goes `DIRTY`/`BEHIND`/`BLOCKED` (common when
epic members edit the same files) sits silently forever and the engine reports
success. This exact failure occurred shipping PR #160 in this repo.

### Details

- **build Phase 6 (skill prose + `ship-changes-as-prs`):** after arming
  auto-merge, read `mergeStateStatus` once; if not `CLEAN`/`UNSTABLE`, reconcile
  by merging `origin/main` in the worktree and re-pushing (re-posting the
  semantic-review gate on the new head), or surface a non-trivial conflict as a
  blocker — never leave `--auto` waiting on an impossible merge.
- **build Phase 7 (skill prose + `ship-changes-as-prs`):** watch this PR to a
  terminal state, polling `state` and `mergeStateStatus` together; a transition
  to `DIRTY`/`BEHIND`/`BLOCKED` is acted on within a poll cycle just like
  `MERGED` ends the watch; the close-out waits for this PR's `MERGED` before
  pruning/pulling/epic-sync, and never blocks on another PR's state.
- **review guardrail (`ship-changes-as-prs`):** a review finding either blocks
  the original PR before merge or becomes a newly planned change against current
  `main` — never a follow-up PR on an already-squash-merged branch.
- **`epic-autopilot/pipeline-stage-execution` + `autopilot.py`:** when the
  pipeline completes with the worktree present, a PR that is not merged parks the
  member as needs-human (stage `merge`) with its URL and session id, instead of
  recording `shipped`.

Affected capabilities: `build-spec-lifecycle` (modified), `epic-autopilot`
(modified). Impact: `plugins/s/skills/build/SKILL.md` (Phases 6–7),
`plugins/s/skills/build/scripts/autopilot.py`, its tests under
`plugins/s/skills/build/tests/`, and the plugin version bump.

### Non-goals

- **GitHub merge queue** is the strongest structural backstop but is repo
  branch-protection config, not a plugin artifact — recommended, out of scope
  here.
- No engine-side polling of a member PR to `MERGED`; the driven session owns the
  waiting (build Phase 7), the engine only classifies the end state.
- No change to member ordering, the three-strike loop, or the gate/enrich flow.

## Implementation

- **Serialization comes from Phase 7 waiting, not new engine code.** The driven
  `/s:build` blocks until its own PR reaches `MERGED` before returning, so the
  autopilot's existing *sequential* member loop lands each member on a `main`
  that already carries the prior member — the next member's build-start
  supersession fetch then sees it. Rejected: an explicit poll/pull-main loop in
  `autopilot.py` — duplicates the driven session's watch and adds engine surface
  the answers scoped out.
- **`merged=False` at drive end is now park-worthy, not shipped.** Because
  Phase 7 waits for the merge, a member whose worktree is still present but whose
  PR is not merged when the pipeline completes is a real problem (a timed-out or
  early-exited session), so `drive_member`'s final resolution parks it
  needs-human at stage `merge` with the PR URL and last session id instead of
  `MemberResult(outcome="shipped", merged=False)`. The vanished-worktree path is
  unchanged (a merged PR still records an early ship). Reuses the existing park
  machinery — no new outcome vocabulary.
- **Conflict boundary differs by attendance.** Both interactive and unattended
  builds attempt a clean `git merge origin/main`; on a non-trivial conflict an
  interactive build surfaces a blocker to the human while an unattended autopilot
  member auto-parks — the same needs-human/stage=`merge` park. Rejected:
  stop-and-ask on every conflict — defeats unattended delivery on any shared-file
  collision.
- **Terminal-state watch, not closure-only.** Phase 7 polls `state` and
  `mergeStateStatus` together so a stuck transition is a first-class terminal
  signal within a poll cycle; the watch is per-PR so one stuck PR never delays
  another change's close-out.

Risk: a re-push after reconciling invalidates the `semantic-review` status, so
the flow must re-post the gate on the new head (already the repo's rule) — the
spec makes it explicit. Risk: a driven session that ignores the Phase-7 wait
regresses to today's behavior; the engine's un-merged→park classification is the
backstop that keeps the failure visible.
