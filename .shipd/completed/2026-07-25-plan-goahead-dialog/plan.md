# plan-goahead-dialog
Status: verified

## Idea

The 0.2.12 findings checkpoint works — the digest and requested diagram now
render before any questioning — but the turn ends in a bare stop, leaving the
user to guess that a typed "go ahead" continues the flow. The user wants the
checkpoint to end in an explicit question: is the picture clear, with a
recommended way to proceed.

Fix: the investigation turn now ends with a single **go-ahead dialog** — an
AskUserQuestion issued after the digest, in the same turn, whose only subject
is how to proceed ("Clear — run the depth gate and continue" recommended
first, "Adjust scope first", "Stop here"). Decision-resolving questions
remain banned from the investigation turn, and the go-ahead dialog is valid
only after the digest has been printed as response text in that turn — the
dialog itself refers to "the findings above", which do not exist unless the
digest was emitted.

### Non-goals

- No return of planning questions to the investigation turn: the go-ahead
  dialog carries no architecture/content/PDF-style decisions — those stay in
  the post-gate rounds.
- No change to the digest content contract, the depth gate, the grill loop,
  or emission.

Affected capabilities: `shipd-plan` (modified — `investigation-findings-digest`).
Impact: `plugins/s/skills/plan/SKILL.md`,
`plugins/s/.claude-plugin/plugin.json`.

## Implementation

- **The dialog is scope-locked by construction.** Flow step 2 ends: print the
  digest (+ requested diagram), then issue one AskUserQuestion asking whether
  the findings and proposed shape are clear enough to proceed — options
  exactly: proceed (recommended, first), adjust scope (user supplies what to
  change via notes/Other), stop. Any other question in that dialog is a
  protocol violation. Rationale: the regression risk of re-admitting
  AskUserQuestion to this turn is a model skipping the digest and asking
  planning questions cold; a dialog that may only reference "the findings
  above" is useless without the digest, and the planning-question ban stays
  explicit.
- **Digest-first stays a stated precondition.** The step keeps its ordering
  rule: the go-ahead dialog may only follow the printed digest in the same
  turn; if the digest has not been printed, printing it comes first.
- **On "adjust scope"**, fold the user's notes into the understanding and
  re-print a delta of what changed before proceeding (or re-investigate if
  the change demands it); on "stop", end the session's planning politely.
- **Version bump to 0.2.13** in `plugins/s/.claude-plugin/plugin.json`, same
  PR, per the cache-snapshot rule in AGENTS.md.

Risks: re-admitting a question call to the investigation turn re-opens the
skip-the-prose failure in principle; accepted deliberately by the user for
the UX gain, and mitigated by the scope lock (a proceed-only dialog is
self-evidently broken without the findings it refers to) and by the
still-banned planning questions. If regression is observed, the fallback is
reverting to the 0.2.12 bare stop.
