# epic-state-across-worktrees
Status: verified
Theme: reliability

## Idea

Make a stub member's derived state see changes planned in sibling worktrees, so
an epic's roster is the same whether the change lives in the main checkout or in
`.worktrees/<member>/`.

### Motivation

`_member_state` (`spec_status.py:672-683`) reads only the invocation root's
`completed/` and `planned/`, so a member planned in its own worktree derives
`unplanned`: run from the main checkout, `_member_state('.', 'shipd-port-tool')`
returns `'unplanned'` while `locate shipd-port-tool` returns `status: ready`.
Autopilot inherits that answer and would re-plan seven already-planned changes.

### Details

- Extend `_member_state` to probe `.worktrees/<name>/` after the invocation root,
  in sorted name order, exactly as `cmd_locate` already does.
- First hit wins, root first: `archived` when that candidate has a matching
  `completed/*-<slug>/`, else its plan status when it has `planned/<slug>/`.
- Add tests covering a worktree-planned member, root precedence, and the
  unchanged `unplanned` fallback.

Affected capabilities: `spec-status` (modified). Impact:
`plugins/s/skills/build/scripts/spec_status.py`,
`plugins/s/skills/build/tests/test_spec_status.py`, and the plugin version bump.

### Non-goals

- No change to `dashboard.py`. It already scans `.worktrees/` (lines 229-235,
  586-592) and shows worktree-planned members correctly; this change brings the
  status CLI up to the board's behavior, not the other way round.
- No change to `autopilot.py`. It consumes `_member_state` through
  `parse_members`, so it inherits the fix with no edit.
- No new flag or opt-in. The probe is unconditional — a caller should not have to
  know whether a change happens to live in a worktree.
- No recursion. Only one level of `.worktrees/<name>/` is probed, matching
  `cmd_locate`; a worktree inside a worktree is not a supported layout.

## Implementation

- **Reuse `cmd_locate`'s probe order verbatim: invocation root first, then each
  `.worktrees/<name>` in sorted name order.** Two functions answering "where does
  this change live" with different orders would be a worse bug than the one being
  fixed. Rejected: scanning worktrees first — the main checkout is the
  authoritative copy once a change has merged.

- **First hit wins, and each candidate is evaluated whole.** For each candidate
  root in order: a matching `completed/*-<slug>/` yields `archived`; otherwise a
  `planned/<slug>/` yields that change's plan status; otherwise move to the next
  candidate. Only when every candidate misses does the result stay `unplanned`.
  Evaluating `archived` across *all* candidates before considering any `planned`
  was rejected: it would let a stale worktree archive outrank the main checkout's
  live plan.

- **A worktree carrying its own `.shipd-config.json` resolves its own content
  directory.** `cmd_locate` already does this by calling `sc.specs_dir(candidate)`
  per candidate rather than reusing the invocation root's; the probe here does the
  same, so a worktree that renamed its content directory is still read correctly.
  A `ConfigError` from a malformed worktree config skips that candidate rather
  than raising, matching `cmd_locate`'s behavior.

- **Epic status derivation is left alone and does not shift for the current
  tree.** `_derive_epic_status` is unchanged; only its inputs get more accurate.
  Verified by running it: `['ready']*7` still derives `ready`, so `shipd-port`
  does not flip when its seven members start reporting `ready`. A member that is
  genuinely `active` in a worktree will now correctly derive `active` — that is
  the intended correction, not a regression.

- **The fix only changes behavior from the main checkout, by construction.** A
  worktree has no nested `.worktrees/` directory, so `_member_state` invoked
  inside one probes exactly what it probes today. That matters because
  `epic-sync` runs in a fresh `epic-close-<slug>` worktree: its derivation is
  unaffected, and the close-out keeps reading the merged main state.

Risk: an epic member could now derive a state from a worktree whose branch is
never merged, making an abandoned worktree look like progress. That is the same
exposure `locate` and the delivery board already carry, and the remedy is the
existing guarded `worktree.sh remove`, not a divergent state rule here.
