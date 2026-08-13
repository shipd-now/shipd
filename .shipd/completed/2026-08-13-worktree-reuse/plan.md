# worktree-reuse
Status: verified
Theme: reliability

## Idea

Make `worktree.sh <change>` idempotent: reuse the change's existing worktree, or
re-attach its existing branch, instead of erroring.

### Motivation

`worktree.sh` (line 186) exits 1 with `error: .worktrees/<change> already exists`
on a second invocation, so any flow that re-enters a change — a resumed
`/s:autopilot` in-session drive, a re-run `/s:build` — hard-fails at its first
step. The `autopilot-in-session` change had to work around this with a caller-side
`[ -d ]` guard that every other caller still lacks.

### Details

- Reuse the worktree when `.worktrees/<change>` already exists and is checked out
  on `change/<change>`: print where to continue and exit 0.
- Create the worktree from the existing branch when `change/<change>` exists but
  its worktree does not — the state left behind by `remove`.
- Keep refusing, non-zero, when `.worktrees/<change>` exists on some *other*
  branch; that is a genuine conflict, not a re-entry.
- Add tests covering all three cases.
- Drop the now-redundant caller-side guard in the autopilot skill.

Affected capabilities: `build-spec-lifecycle` (modified). Impact:
`plugins/s/skills/build/scripts/worktree.sh`,
`plugins/s/skills/build/tests/test_worktree.py`,
`plugins/s/skills/autopilot/SKILL.md`, and the plugin version bump.

### Non-goals

- No change to the `remove` verb, its guards, or `--force`.
- No new flag. Idempotence is the bare invocation's behavior, not an opt-in —
  an opt-in would leave the same trap for every caller that forgets it.
- No reuse across a branch mismatch. A worktree on the wrong branch still errors.
- No change to the not-run-from-a-repository-root error.

## Implementation

- **Idempotence is the default, not a `--reuse` flag.** A flag would preserve the
  trap for every caller that forgets it — which is exactly how this bug reached
  production in `autopilot-in-session`. Rejected: `--reuse`; the safety the
  current error provides is real only for the branch-mismatch case, which stays
  an error.

- **Three cases, decided in this order.** The script resolves `.worktrees/<change>`
  and `change/<change>` and branches:
  | worktree dir | branch | behavior |
  | --- | --- | --- |
  | exists, on `change/<change>` | exists | reuse: print the continue message, exit 0 |
  | absent | exists | create the worktree from the existing branch, exit 0 |
  | absent | absent | create both, exit 0 (today's behavior) |
  | exists, on another branch | any | error, exit non-zero, change nothing |

- **The branch-exists-without-worktree case is the `remove` aftermath.** `remove`
  prunes the worktree but leaves `change/<change>` behind, so re-entering a change
  after a removal currently errors on a branch the user still wants. Attaching to
  it is what every caller means; the branch name is deterministic per change, so
  there is no ambiguity about which branch to attach.

- **Reuse prints the same continue message as creation.** A caller cannot tell
  the two apart from the exit code, and should not need to: the postcondition is
  identical — a worktree at `.worktrees/<change>` on `change/<change>`, ready to
  work in. Printing a distinguishing line (`reusing …`) is fine; changing the
  message's shape is not, since skills quote it.

- **Bash 3.2-safe, per the constitution.** The added logic uses `git -C` and
  `git rev-parse --abbrev-ref HEAD` with plain `if`/`case` — no associative
  arrays, no `mapfile`.

- **The autopilot skill's caller-side guard comes out.** `autopilot-in-session`
  added an `if [ ! -d ".worktrees/<member>" ]` wrapper precisely because the
  script was not idempotent. Leaving it would be harmless but would enshrine the
  workaround as the pattern other skills copy.

Risk: a caller that today *relies* on the error to detect an existing worktree
would silently proceed instead. Verified against the tree: grepping the skills
and agent definitions for `already exists` returns the autopilot guard this
change removes (`plugins/s/skills/autopilot/SKILL.md:161-171`) and unrelated
uses of the phrase about changes and video bundles — no other reader of the
worktree error.
