# multi-agent-pr-doc-trim
Status: verified
Planned-at: d818c8d6a072a9f1e2b1cefb9c60c9c160460cf8
Gated-hash: 9984a735739c

## Idea

Trim `docs/multi-agent-pr.md` to its concepts and drop the note that explains
Mermaid syntax.

### Motivation

Readers of the Multi-agent PR page hit a sentence about Mermaid state names and
hyphens that tells them nothing about the room. The maintainer calls it
distracting cruft and wants the page simplified.

### Details

- Label the diagram state `input-required` through a Mermaid alias, so the
  diagram shows the real name and needs no explanation.
- Drop the diagram's two self-loops (`working --> working`,
  `input_required --> input_required`).
- Cut the prose that restates the diagram ("A task opens at...", "Any open task
  can move to...").
- Cut filler: the intro line of "Two ways a turn runs", "Both paths read and
  write the room through the same verbs", and "The round cap bounds each task".
- Fold "Who acts when" into one lead sentence and two short bullets.

Affected capability: `shipd-room` (modified, `room-skill-docs`). Impact:
`docs/multi-agent-pr.md` only.

### Non-goals

- No change to the room protocol, its verbs, or any other room doc.
- No edit to the website repo; its docs sync picks the page up on its own.

## Implementation

- The exact target text lives in `artefacts/multi-agent-pr.md`; the builder
  copies it verbatim. It lints clean at 89 lines.
- Keep the diagram, aliased with `state "input-required" as input`. Rejected:
  deleting the diagram for a state list, because the diagram carries the
  transitions in one glance. Rejected: keeping `input_required` and deleting
  only the note, because the diagram would then show a name the protocol never
  uses.
- Drop self-loops: a Message that keeps a task's state is not a transition a
  concept reader needs.
- The delta adds one sentence and one scenario to `room-skill-docs`; every
  existing clause still holds, since the trimmed page names all six states,
  `room.max_rounds`, `/s:room`, `shipd copilot add --room`, and all links.

Risk: the alias fails to render. Task 1.4 renders the block before the change
ships.

## Readiness attestation

### Problem and motivation

The page explains Mermaid syntax to readers, and the maintainer named that
sentence as cruft.

Evidence:

- `docs/multi-agent-pr.md:45-48` holds the hyphen note and the restated
  transitions.
- The request names the sentence and asks for the page to be simplified.

### Scope and non-goals

One doc changes; the protocol and the website repo stay untouched.

Evidence:

- In scope: `docs/multi-agent-pr.md:1-100`.
- Out of scope: `shipd-now-website/scripts/sync-docs.mjs` vendors the page from
  this repo, so the website needs no edit.

### Affected capabilities and files

One capability and one file are affected, because `room-skill-docs` pins this
page's content.

Evidence:

- Capability `shipd-room`: requirement `room-skill-docs` (base a17886be013a),
  hash from `spec_status.py base-hash shipd-room room-skill-docs`.
- File: `docs/multi-agent-pr.md`.
- Runnable premise: `docs_lint.py docs/multi-agent-pr.md` exits 0 today, and
  `docs_lint.py artefacts/multi-agent-pr.md` exits 0 with no warnings.
- Runnable premise: a local Mermaid render could not run, since
  `mermaid-isomorphic` found no Playwright browser; task 1.4 renders it at
  build time.

### No open task-shaping decision

Every decision is settled by investigation; none went to the oracle or the user.

Evidence:

- Diagram kept and aliased, over a plain state list: settled by investigation,
  since the spec requires only that the page names the six states.
- No test pins the old text: `grep` over `plugins` and `tests` found no test
  that reads `docs/multi-agent-pr.md`.
