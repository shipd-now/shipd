# plan-ask-mikk
Status: verified
Epic: mikk-knowledge

## Idea

Insert the ask-mikk oracle as the middle rung of `/s:plan`'s escalation
ladder: un-inferrable decisions are put to the `s:oracle` agent before any
user question round, and only what the oracle cannot answer goes to the user.

### Motivation

Plan's only move at an un-inferrable decision is a user question round, even
when the workspace wiki already holds mikk's standing answer. The epic's
oracle read path shipped in `ask-mikk-oracle`, but no planning surface
consults it yet, so escalations never get cheaper.

### Details

- `plugins/s/skills/plan/SKILL.md` gains an ask-mikk-rung section: before any
  user question round — the fast path's batched round, a depth-path round, or
  enrichment's true-gap round — each remaining un-inferrable decision is
  shaped into a compact question and put to one `s:oracle` spawn per
  decision, in parallel.
- `ANSWER` verdicts fold in as resolved and are reported visibly with their
  citations; `INSUFFICIENT` decisions go to the user unchanged (the oracle has
  already queued them); a failed spawn or malformed verdict degrades to
  `INSUFFICIENT` — the rung never blocks planning.
- `plugins/s/skills/plan/references/readiness.md` gains the middle rung in
  "How to use the gate": investigate, then consult ask-mikk, then ask the
  user.
- `plugins/s/skills/plan/references/dialogue.md` routes decisions surviving
  the fact/decision test through the rung before the grouped rounds.
- Plugin version bumps to the next free patch above `origin/main` at ship
  time (0.6.10 as of enrichment).

Affected capabilities: `shipd-plan` (modified). Impact:
`plugins/s/skills/plan/SKILL.md`,
`plugins/s/skills/plan/references/readiness.md`,
`plugins/s/skills/plan/references/dialogue.md`,
`plugins/s/.claude-plugin/plugin.json`. Prose only —
no engine scripts change; the oracle contract (`shipd-ask`) is consumed, not
modified.

### Non-goals

- No oracle consultation in the investigation turn: the digest's OPEN
  QUESTIONS ending stays oracle-free — open questions reach the rung in the
  post-gate rounds.
- No autopilot-side integration — that is the `autopilot-ask-mikk` member.
- No queue answer write-back: the engine has no such verb; answers reach the
  wiki through teach-mikk's drain.
- No changes to the oracle agent, `/s:ask`, or any engine script.

## Implementation

- **Consult point.** After the depth gate, at the moment a user question round
  would otherwise open — stated once, path-neutrally, in a new SKILL.md
  section that the fast-path contract, the depth path (`dialogue.md`), and
  enrichment's true-gap step all point at. Rejected: consulting during
  investigation — the epic binds the consult to "before opening a user
  question round", digest open questions flow into the post-gate rounds
  anyway, and this keeps agent-spawn latency out of the investigation turn.
- **Spawn shape.** One `s:oracle` spawn per decision (the epic's
  compact-question contract binds one decision-ready unit per spawn), issued
  in parallel via the Agent tool with `subagent_type: s:oracle`, passing the
  compact question (decision / concrete options / the recommendation plan
  already forms as its default), the repo's absolute root, and the status CLI
  path — the exact spawn pattern `/s:ask` established.
- **Verdict handling.** Branch on the first non-blank line. `ANSWER` → the
  decision is resolved; `INSUFFICIENT` → the decision enters the user round as
  today; anything else (spawn failure, malformed first line) is treated as
  `INSUFFICIENT`. Rejected: erroring on a bad verdict — the epic's ladder
  decision says the oracle never blocks its caller, so neither may the rung.
- **Visibility and authority.** Oracle-settled decisions are reported in
  user-visible text with the oracle's position and `Cited:` sources — in the
  context brief when a round still opens, or in the status text before
  proceeding when nothing remains to ask — and a typed user override always
  supersedes the oracle. The user stays the final authority the wiki merely
  caches.
- **Risks.** A stale or wrong wiki answer steering the plan — guarded by the
  visibility/veto rule above. Driven or fixture sessions with no workspace
  (evals) — the oracle degrades to repo surfaces and `Queued: none`, so the
  flow behaves as today; the local eval run exercises exactly this path.
