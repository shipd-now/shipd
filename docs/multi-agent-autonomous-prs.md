<!-- doc-type: how-to -->

# Run multi-agent autonomous pull requests

Two agents and shipd's CI reviewer can carry a pull request from opened to
merged with no human turn. The author agent fixes, two reviewers approve, and
GitHub merges. This guide sets up both listeners in any repository.

The worked example is
[unkannybanny #40](https://github.com/mikkel-bergmann/unkannybanny/pull/40).
Its two agents took it from opened to merged in under 20 minutes.

## The actors

- **The author agent** joins the room, asks for a review, fixes findings,
  and pushes.
- **The room reviewer agent** reviews each head with `/s:review` and approves
  it, or files findings to the author.
- **The CI reviewer** is the `semantic-review` gate in GitHub Actions. It
  reviews each push and approves it or asks for changes.
- **GitHub** enforces the merge rules and merges the pull request once they
  hold.

## Before you start

- You have installed the review gate with `/s:gate`.
- Your merge rules require two approvals plus the `ci` and `semantic-review`
  checks. The `merge` key in `.shipd-config.json` declares them, and those
  are its defaults. Apply them with `shipd gate rules apply`.
- The reviewer has its own GitHub account with push permission on the
  repository, and its own `GH_CONFIG_DIR`. See
  [Give an agent its own GitHub account](agent-identity.md).
- You have signed in to Claude Code on each machine that runs a listener.

The examples use `<owner>/<name>` for the repository, `author-a` for the
author agent, and `reviewer-b` for the reviewer agent.

## Start the reviewer listener

Open a terminal in a checkout of the repository. Run one reviewer for the
whole repository, on the reviewer's account:

```sh
GH_CONFIG_DIR=~/.config/gh-reviewer shipd room run --repo <owner>/<name> --role reviewer --agent reviewer-b
```

- The listener answers every open pull request with a task for `reviewer-b`.
  It spends no tokens while it waits.
- A lock allows one runner per agent per machine. A second run refuses to
  start.
- Across machines, review claims keep it to one review per head. Claims
  need plugin version `0.6.345` or later on every reviewer runner.

[Run two agents on a pull request unattended](room-run.md) lists the limits
and the result line.

## Start the author listener

Open a terminal in a checkout of the pull request's branch, on the author's
own `gh` login. Run:

```sh
shipd room run <pr> --repo <owner>/<name> --role author --agent author-a --request-review reviewer-b
```

- The listener joins the room and opens one review task for `reviewer-b`.
- It takes a turn on each finding: it fixes the code and pushes, or replies
  with a reason.
- After each push, it opens one re-review task for each reviewer.
- It also takes a turn on a "Fix required" review from the CI reviewer.

## Watch the flow

Each step states the general rule, then the #40 instance in brackets.

1. The author opens the pull request, arms auto-merge, joins the room, and
   asks for a review. [`author-a` joined and addressed `reviewer-b` at head
   `70a85ba`.]
2. The CI reviewer reviews the head and asks for changes on a blocking
   finding. [It requested changes on `70a85ba`.]
3. The room reviewer claims the head, reviews it, and approves it or files
   findings. [`reviewer-b` approved with three low findings.]
4. The author takes a turn on the findings, fixes the code, and pushes.
   [`author-a` pushed `a9877ec`.]
5. GitHub dismisses the approval on the old head, because the merge rules
   dismiss stale approvals. [GitHub dismissed the approval of `70a85ba`.]
6. The CI reviewer reviews the new head and approves it. [It approved
   `a9877ec`.]
7. The author listener sees the moved head and opens a re-review task.
   [`author-a` asked `reviewer-b` to re-review `a9877ec`.]
8. The room reviewer reviews the new head and approves it. [`reviewer-b`
   approved `a9877ec`.]
9. GitHub merges the pull request once two approvals and every required check
   hold. [#40 squash-merged and deleted its branch.]

## One review per head

A reviewer runner claims a head before it reviews it, through a git ref on
GitHub. GitHub creates the ref only once, so exactly one runner posts each
review. The claim also sets the commit status `room-review/<agent>` on the
head.

To make merges wait for the claimed review, add that context to the merge
rules, then run `shipd gate rules apply`:

```json
{"merge": {"required_checks": ["ci", "semantic-review", "room-review/reviewer-b"]}}
```

[Review claims](room-review-claims.md) covers takeover and the poster fence.

## When something stalls

- **The runner refuses to start with `another room run already serves`.**
  Another run of the same agent holds the lock on this machine. Stop that
  run, or keep it.
- **The reviewer refuses to start on push permission.** Its account cannot
  create the claim ref. Give that account write access to the repository.
- **The pull request stays blocked.** Run `gh pr checks <pr>` for a missing
  check, then resolve every open review thread. Each required check must pass
  on the current head.

## See also

- [Run two agents on a pull request unattended](room-run.md) — every flag and
  the result line.
- [Give an agent its own GitHub account](agent-identity.md) — the reviewer's
  account.
- [Run an agent's turn in a multi-agent PR](pr-room.md) — the room verbs.
- [Review claims](room-review-claims.md) — one review per head.
- [Room wake reference](room-wake-reference.md) — the Actions wake.
- [Multi-agent PR](multi-agent-pr.md) — the room model.
- [Copilot review](copilot-review.md) — the CI reviewer's workflow.
