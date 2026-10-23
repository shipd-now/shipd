# multi-agent-walkthrough
Status: verified
Planned-at: 64698701c95469721426884381f71733de952969
Gated-hash: 6766b4a51a28

## Idea

Write one how-to, "Run multi-agent autonomous pull requests", that takes a
reader from nothing to a pull request two agents review, fix and merge on
their own, using unkannybanny #40 as the worked example.

### Motivation

The website's landing section now animates a real multi-agent pull request.
Today a reader who wants to run one has to stitch the setup together from
five separate room docs, none of which shows the whole flow end to end.

### Details

- New `docs/multi-agent-autonomous-prs.md`, doc type `how-to`, at most 150
  lines. It is written for any repository, and unkannybanny #40 appears only
  as an example.
- It covers the four actors, the prerequisites, and setting up each listener
  (the reviewer runner, the author runner). It then walks the flow step by
  step against #40, covers review claims and the merge guard, and ends with
  where to go next.
- It links to the existing pages for depth and repeats none of their detail:
  `docs/room-run.md`, `docs/agent-identity.md`, `docs/pr-room.md`,
  `docs/room-review-claims.md`, `docs/room-wake-reference.md`,
  `docs/multi-agent-pr.md` and `docs/copilot-review.md`.
- `docs/multi-agent-pr.md` and `docs/room-run.md` each gain one line in their
  `## See also` section pointing at the new page.

Affected capability: `shipd-room` (added `multi-agent-walkthrough-doc`).
Impact: `docs/multi-agent-autonomous-prs.md`, `docs/multi-agent-pr.md`,
`docs/room-run.md`. There is no plugin change, so no version bump.

### Non-goals

- No change to the room scripts or their behaviour.
- No website change; the `multi-agent-docs-section` change in the website
  repository publishes the page.
- No rewrite of the existing room docs.

## Implementation

- **Authoring.** Write the page through `/s:document`. It must pass
  `docs_lint.py` and stay at or under the 150-line `how-to` cap. Line 1 is
  `<!-- doc-type: how-to -->`, and the title is
  `# Run multi-agent autonomous pull requests`.
- **Outline.** Use these sections, in order:
  1. A 2–3 sentence opener: two agents and shipd's CI reviewer take a pull
     request from opened to merged with no human turn.
  2. `## The actors`: the author agent, the room reviewer agent, the CI
     reviewer (the `semantic-review` gate in GitHub Actions) and GitHub,
     which enforces the merge rules. Each gets one line saying what it does.
  3. `## Before you start`:
     - The review gate is installed with `/s:gate`.
     - The merge rules require two approvals plus `ci` and `semantic-review`
       (`merge.required_checks`, then `shipd gate rules apply`).
     - The reviewer has its own GitHub account with push permission and a
       `GH_CONFIG_DIR` (link `agent-identity.md`).
     - Claude Code is signed in on each machine that runs a listener.
  4. `## Start the reviewer listener`: the repo-wide command,
     `GH_CONFIG_DIR=<reviewer config> shipd room run --repo <owner>/<name>
     --role reviewer --agent <reviewer>`. Say:
     - it answers every open pull request;
     - one runner per agent per machine is enforced by a lock;
     - across machines, review claims keep it to one review per head.

     Link `room-run.md`.
  5. `## Start the author listener`: from a checkout on the pull request's
     branch, `shipd room run <pr> --repo <owner>/<name> --role author --agent
     <author> --request-review <reviewer>`. Say:
     - it joins the room and asks for the review;
     - it fixes findings and pushes;
     - it asks for a re-review after each push.
  6. `## Watch the flow`: a numbered walk through the steps, each with one
     sentence of the general rule and the #40 instance in brackets:
     - open, join, auto-merge armed, review request;
     - the CI reviewer asks for changes;
     - the room reviewer reviews;
     - the author pushes a fix;
     - the stale review is dismissed;
     - the CI reviewer approves;
     - the re-review request;
     - the room reviewer approves;
     - merge.

     Link https://github.com/mikkel-bergmann/unkannybanny/pull/40.
  7. `## One review per head`: claims in two to four sentences, plus how to
     make merges wait for the claimed review by adding
     `room-review/<reviewer>` to `merge.required_checks`. Link
     `room-review-claims.md`.
  8. `## When something stalls`: three bullets. A runner refused by the
     lock, a reviewer without push permission, and a merge blocked on an
     unresolved thread or a missing check. Each gets its fix.
  9. `## See also`: the room docs listed under Details.
- **Commands.** Every command in the page must match the CLI as it is today.
  Check each against `shipd room run --help` output before writing it.

## Questions and answers

### Q1: Which page does the landing link open?
- **Question:** Options: (a) a new walkthrough page that links on to the room
  docs; (b) publish `multi-agent-pr.md` unchanged; (c) rework
  `multi-agent-pr.md`. Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (a), kept general. Use PR 40 as an example, make the
  instructions apply to any repository, and explain how to set up the agent
  listeners.
- **Queued:** q-multi-agent-pr-docs-link-target

## Readiness attestation

### Problem and motivation

No single doc shows a multi-agent pull request end to end, with its setup.

Evidence:

- `docs/room-run.md` (how-to), `docs/agent-identity.md` (how-to),
  `docs/pr-room.md` (how-to), `docs/room-review-claims.md` (concept),
  `docs/multi-agent-pr.md` (concept): each covers one part.

### Scope and non-goals

One new how-to and two See also lines.

Evidence:

- In scope: the three files under Details.
- Out of scope: scripts and the website.

### Affected capabilities and files

`shipd-room` gains `multi-agent-walkthrough-doc`.

Evidence:

- `.shipd/verified/shipd-room/spec.md` already holds the room's doc
  requirements.
- The doc standard caps `how-to` at 150 lines
  (`plugins/s/skills/document/references/standard.md`).

### No open task-shaping decision

The user chose a general walkthrough with #40 as the example, including the
listener setup.

Evidence:

- Q1.
