# room-join-owns-its-card
Status: verified
Epic: pr-conversations
Planned-at: 4dbd39712940f796520736363a14f1de45156124
Gated-hash: 046f2f2f557d

## Idea

Make `shipd room join` edit only a comment that holds nothing but the agent's own card.

### Motivation

On https://github.com/mikkel-bergmann/unkannybanny/pull/14 the reviewer agent's `room join` overwrote the gate's review summary comment, so the pull request lost its review summary. Every later room verb that trusts a card's comment id carries the same risk.

### Details

- `join` PATCHes a comment only when its sole room marker is this agent's card and it carries no semantic-review summary marker.
- Otherwise `join` POSTs the card as its own comment.
- A rejoin finds that own comment and edits it.

Affected capabilities: `pr-room` (modified: `room-join-verb`). Impact: `plugins/s/skills/room/scripts/room.py`, `plugins/s/skills/room/tests/test_room.py`, `docs/pr-room.md`, and the plugin version.

### Non-goals

- No change to card rendering, the `role` field, or the speaker heading; `room-speaker-identity` owns those.
- No change to `list`, `watch`, `message`, or `close`, which still read cards through `_parse_room`.
- No cleanup of comments already overwritten on existing pull requests.

## Implementation

- **Ownership is decided by markers.** `room.py` gains `_owned_card_ids(comments)`: for each issue-endpoint comment, parse with `room_schema.parse_comments`; the comment is owned only when it yields exactly one object, an `AgentCard`, and the body has neither `<!-- shipd-semantic-review -->` nor the legacy `<!-- am-semantic-review -->`. The result maps card name to the last owned comment id. Rejected: an author-login test, which needs `gh api user` and is not in the epic's rule (Q1).
- **`cmd_join` uses it.** It reads comments once through `_read_room`, PATCHes `owned[agent]` when present, else POSTs. The stdout JSON and stderr line are unchanged (Q2).
- **`_parse_room`'s `raw` stays.** Other code and tests read it; narrowing `join` alone is the smallest change. A card inside a foreign comment still counts as the agent's card for `list`, `message`, and `close`, since the gate's agent has joined in that sense.
- **Epic Decision relied on.** "A room verb edits only what it owns" in `pr-conversations`.
- **Version.** One patch above `main`'s `plugins/s/.claude-plugin/plugin.json` at build time.

Risk: a hand-edited card comment with extra text but one marker stays owned; that is intended. Risk: the legacy marker is refused too, a safe superset of the epic's wording.

## Questions and answers

### Q1: How is a comment's ownership tested?
- **Question:** Should `join` treat a comment as owned by marker alone (one AgentCard marker naming the agent, no semantic-review summary marker), or also require the comment's author login to match the posting login? Options: (1) marker only; (2) marker plus author login. Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Marker only. A comment is owned when its sole room marker is this agent's AgentCard and it carries no `shipd-semantic-review` marker; no author-login check or extra `gh api user` call. The oracle noted that also refusing the legacy `am-semantic-review` marker is a safe superset, which this plan adopts.
- **Cited:** epic/pr-conversations

### Q2: Does join signal the foreign comment it left alone?
- **Question:** When the agent's card lives only inside another comment and `join` posts its own card, should it say so? Options: (1) no change to the stdout JSON or the stderr line; (2) add a stderr note or JSON field naming the untouched comment. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) No change. The printed `comment` is the new comment's id and the stderr line stays `joined <context> as <name>`; a caller gains nothing from a field that no verb reads, and the shape stays stable for the wake and the skill.
- **Queued:** q-room-join-foreign-card-signal

## Readiness attestation

### Problem and motivation

`join` overwrote the gate's review summary on PR 14, and the epic requires that no verb edit a comment it did not author for that purpose.

Evidence:

- https://github.com/mikkel-bergmann/unkannybanny/pull/14 comment 6206725970 carried the gate's `shipd-room-card` and the `shipd-semantic-review` marker and was replaced by the join card.
- `plugins/s/skills/room/scripts/room.py` `cmd_join` PATCHes `raw[agent]`, and `_parse_room` fills `raw` from any issue comment holding the card.

### Scope and non-goals

The change narrows `join`'s edit target and nothing else.

Evidence:

- In scope: `cmd_join` and a new helper in `room.py`, its tests, one doc sentence, the version.
- Out of scope: card rendering and heading (`room-speaker-identity`), other verbs.

### Affected capabilities and files

One capability, one modified requirement.

Evidence:

- `pr-room`: `room-join-verb` (base 9afef40619e1), from `spec_status.py base-hash pr-room room-join-verb`.
- Files: `plugins/s/skills/room/scripts/room.py`, `plugins/s/skills/room/tests/test_room.py`, `docs/pr-room.md`, `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `python3 spec_status.py base-hash pr-room room-join-verb` printed `9afef40619e1`, exit 0.

### No open task-shaping decision

Every task-shaping decision is settled.

Evidence:

- Ownership test: settled by the oracle, Q1.
- Join output shape: settled by the planner default, Q2.
- Fallback to a new comment and the summary-marker protection: settled by the epic Decisions.

Full evidence: /Users/mikkelbergmann/projects/workspaces/shipd/shipd/.worktrees/room-join-owns-its-card/.shipd/planned/room-join-owns-its-card/plan.md
