# /s:build — merge warnings, telemetry, and the post-merge close-out

The long form the router points at. Read it around step 7 (apply) and step 9
(report).

## Merge warnings

`spec_merge.py <change> --json` emits **one JSON object per line** to stdout —
one per merge warning, or no lines at all on a clean merge. Each carries an
`id`, a `kind`, and the detail fields for that kind:

| kind | what it means |
| --- | --- |
| `stale-base` | the delta's `base:` hash no longer matches the master requirement it edits — the master moved after the change was planned |
| `id-collision` | the delta adds a requirement id the master already carries |
| `missing-master` | the delta modifies or removes a requirement the master does not have |

Take-newer means a warning **never fails the merge**: the exit code stays 0 and
the delta is applied. The warning is the load-bearing mitigation, so it has to
reach the report — capture the JSON when you run the merge and render one
`⚠ spec: <id> — <kind>` line per warning between the change header and the
rest of the report. On a clean merge the block is empty; omit it rather than
printing a placeholder.

A `stale-base` or `id-collision` that traces to a merge doing *this plan's
work* is not a warning to note and move past — it is supersession, which the
`check-base` step ahead of implementation exists to catch.

## The report shape

```
Build complete. {summary}
Change: {change} — {done}/{total} tasks, Status: {status}
PR: {pr_url}
{warnings}
{table}

{one short paragraph describing what was built, including the commit hash}

Observations:
{bullet list of actionable items, or the literal line: nothing to note}
```

`{pr_url}` is always the full clickable URL, never the number. Task counts come
from `claim_task.sh status <change>`. Under `pr-mode: draft`, mark the PR as a
draft and say plainly that merging it is a human's step and that the worktree
stays in place.

Telemetry — the token summary and the per-model timing table — is best-effort
in every direction: a failure to produce it is an Observations line, never a
blocker, and a pipeline that declares `telemetry` false prints the same report
without its token blocks.

## Shipping modes

**auto** (no `pr-mode` line, or `pr-mode = "auto"`) — open the pull request
with `gh pr create --fill` and arm `gh pr merge --auto --squash
--delete-branch`. Arming auto-merge is not proof of merge: read
`mergeStateStatus` once afterwards.

| state | what it means | what to do |
| --- | --- | --- |
| `CLEAN`, `UNSTABLE` | on track to merge itself | watch it to a terminal state |
| `BLOCKED`, branch neither behind nor dirty | waiting on a required check | post the review gate if it is not posted, then wait |
| `DIRTY`, `BEHIND` | it cannot merge as armed | `git fetch origin main && git merge origin/main`, push, re-post the review on the new head |

A non-trivial conflict is a blocker to surface, not something to resolve by
guessing.

**draft** (`pr-mode = "draft"`) — open the pull request with
`gh pr create --fill --draft` and arm **no** auto-merge. The open draft is the
terminal state: read no merge state, reconcile nothing, run no watch and no
close-out, and leave the worktree and the branch in place for the human who
merges it. The review gate still posts, so the reviewer sees a disposed
review.

Any other `pr-mode` value stops the ship before pushing: push nothing, open no
pull request, and report that `auto` and `draft` are the accepted values.

## The post-merge close-out (auto mode only)

Once the pull request has actually merged, from the **main checkout**:

```sh
bash "$S/worktree.sh" remove <change>
git switch main && git pull
```

The guarded `remove` verb refuses with exit 2, listing every reason, while the
worktree still shows work in progress — uncommitted files, an unshipped
planned change, an outstanding `[~]` claim, or a file touched inside the idle
window. That refusal is what stops one session pruning another's live
worktree; pass `--force` only once you have confirmed it is spurious.

Then, and only when the change touched the plugin's own tree, refresh the
plugin snapshot from the main checkout so the updated commands load next
session.

**When the change carried an `Epic:` header**, re-derive the epic's status
after the merge — never before it, and never from the main checkout, since a
member only reads as archived on the base branch once the squash merge has
landed:

```sh
bash "$S/worktree.sh" epic-close-<slug> --fresh
python3 "$S/spec_status.py" --root .worktrees/epic-close-<slug> epic-sync <slug>
```

`epic-sync` rewrites the epic file **only when the derived status actually
changes**. If it did, ship that edit as its own auto-merging pull request; if
it did not, remove the close-out worktree and open nothing.
