<!-- doc-type: concept -->

# Review claims

A review claim makes one reviewer runner post the review of one pull request
head. Reviewer runners of one agent can run on several machines. Without a
claim, two of them can review the same head and post two reviews.

## How a runner claims a head

Before a `reviewer` or `ci` turn, the runner creates a git ref on GitHub:
`refs/shipd/claims/pr-<N>/<agent>/<sha>/<gen>`. GitHub creates a ref only
once, so exactly one runner wins each generation. The winner runs the turn.
The other runners skip it and look again at their next poll.

The claim refs are not branches or tags. They show nowhere in the GitHub
interface, and a push to them starts no workflow.

## The heartbeat

While its turn runs, the winner moves its claim ref to a new claim commit
every 60 seconds. GitHub stamps each commit with its own clock. A runner
measures every age as GitHub's time minus that stamp, never its own clock.

## Takeover

A runner takes over a claim in two cases. The holder released the claim after
a turn that posted nothing, or the last heartbeat is more than 10 minutes old.
The taker creates the next generation, again atomically. It never rewrites the
old one, because GitHub enforces no fast-forward on custom refs.

The `done` ref, `refs/shipd/claims/pr-<N>/<agent>/<sha>/done`, marks a
reviewed head. The poster creates it once, and no heartbeat moves it. Other
runners skip that head and move their cursor past the task. A turn that ends
without one releases its claim.

A runner claims only a turn that carries a review request, a task another
agent opened. A turn that replies on its own tasks runs unclaimed.

## The poster fence

The runner passes the won claim to the reviewing session in the
`SHIPD_ROOM_CLAIM` variable. The poster, `review_gate.py post`, checks the
claim twice: before its first GitHub write, and again before it submits the
review. The check passes only when all hold:

- The claim names the current head, and no newer generation or `done` ref
  exists for it.
- The claim ref names this runner as its holder.
- The last heartbeat is under 5 minutes old.

If the first check fails, the poster writes nothing and prints one line
starting `room claim lost` and ending `nothing posted`. If the second fails,
the summary exists but the poster submits no review, and the line ends
`summary posted, review not submitted`. Both exit non-zero. After the second
check passes, the poster creates the `done` ref and sets the merge status to
`success`, whether or not it submitted a review.

A runner that freezes over 5 minutes after the second check can still post late.
The merge status below covers that gap.

## The merge status

A won claim sets the commit status `room-review/<agent>` to `pending` on the
head. The poster sets it to `success` when it finishes. A release leaves it
`pending`.

A repository makes merges wait for the review by listing the context in
`merge.required_checks` in `.shipd-config.json`, then running
`shipd gate rules apply`:

```json
{"merge": {"required_checks": ["ci", "room-review/reviewer-b"]}}
```

With the status required, a head no runner claims blocks the merge.

## Permission

Creating a ref needs push permission. A `reviewer` or `ci` runner whose
account lacks it refuses to start with one `Error:` line, before it joins any
room. An `author` runner needs no claim and no permission.

## Cleanup

When a pull request closes, the runner deletes every claim ref of it. A
failed delete prints a `warning:` line and the run goes on. Each heartbeat
leaves one small commit object, unreachable once the refs are gone.

## Limits

- Runners older than plugin version `0.6.345` do not claim. The guarantee
  holds once every runner of the agent runs this version or a later one.
- The CI gate workflow makes no claim. Its poster runs without
  `SHIPD_ROOM_CLAIM` and behaves as before.

## See also

- [Run two agents on a pull request unattended](room-run.md) — the runner.
- [Semantic review reference](semantic-review-reference.md) — the poster's flags.
