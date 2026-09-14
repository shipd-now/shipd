# docs-semantic-review
Status: verified

## Idea

Document the semantic review as a concept guide, so a reader can learn what
`/s:review` reads and how it rates findings without opening the skill.

### Motivation

The `review-rubric` epic rebuilt the review across five changes, and none of it
reached `docs/`. The two review guides there cover installing and configuring
the Copilot gate; `docs/cheatsheet.md` gives `/s:review` one table row. A reader
who wants to know what the review looks for has nowhere to go.

### Details

- Add `docs/semantic-review.md`, a concept guide covering the `semdiff`
  subcommands, the passes that look past the changed lines, the severity rule
  and its exposure floor, the local and gate paths, and the degradation
  behaviour.
- Repoint `docs/copilot-review.md`'s `/s:review` link from a README anchor to
  the new guide.

Affected capabilities: `project-readme` (one added requirement). Impact:
`docs/semantic-review.md` and `docs/copilot-review.md`. No code changes, and no
plugin version bump — nothing under `plugins/s/` changes.

### Non-goals

- No reference doc. The `--json` finding shape, the `lint` configuration key,
  and the `prior` verb's evidence classes are lookup material for a separate
  `docs/semantic-review-reference.md`.
- No edit to `docs/copilot-review-reference.md`. It sits at its 250-line cap and
  documents the gate's managed files, not the review itself.
- No new row in `docs/cheatsheet.md`. `/s:review` already has one.
- No change to the skill, the engine, or any spec the review implements.

## Implementation

- **Concept, not reference.** The guide explains what the review is and why its
  rules hold. It lists no flags and no JSON fields, which is what keeps it a
  concept doc under the 100-line cap rather than a hybrid. It stands at 97
  lines.

- **One diagram, justified by the structural test.** The doc carries a single
  mermaid flowchart of the two paths a review takes: a local run ends at the
  report, and a posting run enters a loop that survives later pushes. That is a
  lifecycle with a branch, which the standard's test admits. The diagram
  restates no adjacent list or table.

- **Three tables carry what prose would bury.** The subcommands, the severity
  rule, and the blocking column each read better as a row than a sentence.
  Rejected: prose for the severity rule, which hides the one thing a reader
  needs — that `high` and `medium` block and `low` never does.

- **The link repoint stays inside its requirement.** `docs/copilot-review.md`
  pointed `/s:review` at a README anchor, which predates this guide. The
  `copilot-review-guide` requirement pins only that the how-to links to
  `docs/copilot-review-reference.md`, and that link is untouched, so the
  repoint needs no change to that requirement.

- **Risk: the guide drifts as the review changes.** The new requirement names
  the specific claims the doc must carry — the subcommand set, the exposure
  floor, the suppression rule — so a later change to the review that leaves the
  doc stale fails the requirement rather than passing unnoticed.
