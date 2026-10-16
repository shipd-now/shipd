# room-speaker-identity
Status: verified
Epic: pr-conversations
Planned-at: 4dbd39712940f796520736363a14f1de45156124
Gated-hash: 1d81ba3aa81a

## Idea

Open every agent comment, and the gate's review submission, with a heading naming the agent, its role, and the person it acts for.

### Motivation

On https://github.com/mikkel-bergmann/unkannybanny/pull/14 four comments from different agents all posted under one GitHub account and read as one bot repeating itself, so a reader could not tell who said what. The review submission body also repeated a one-line pointer instead of saying who reviewed.

### Details

- Cards gain an optional `role` (`author`, `reviewer`, `ci`), set by `room join --role`.
- Card and agent-message prose open with `### ☕ shipd · <agent> · <role> (for @<login>)`; messages put `→ <to> · <state>` on the next line.
- `join`, `message`, `close`, and `watch` read the login once per verb from `gh api user`; message role comes from the poster's own card.
- `review_gate.py post` submits its review with the same heading and one pointer sentence.

Affected capabilities: `pr-room` (modified: `room-agent-card`, `room-message-shape`; added: `room-join-role`, `room-poster-identity`), `semantic-review` (added: `gate-review-submission-body`). Impact: `plugins/s/skills/room/scripts/room_schema.py`, `room.py`, `plugins/s/skills/review/scripts/review_gate.py`, their tests, the room skill text, the wake workflow, `docs/pr-room.md`, and the plugin version.

### Non-goals

- No change to which comment `join` edits; `room-join-owns-its-card` owns that.
- No heading on the gate's summary comment or inline finding comments, which keep their brand line and markers.
- No `--role` on `message` or `close`, and no GitHub App identities.

## Implementation

- **Renderers take the speaker as arguments.** `room_schema.render_comment(obj, login="", role="")` stays pure. `role` applies to Messages only; a card uses its own `role`. A new `speaker_heading(agent, role="", login="")` builds `☕ shipd · agent[ · role][ (for @login)]` and both `_card_prose` and `_message_prose` use it. Role and login are never written into a Message marker (Q3). Rejected: storing the role in message metadata, which duplicates the card and can drift.
- **Heading is a level-3 markdown heading** (Q1). Card prose: heading, then `<sub>joined the room[ from H][ · skills: ...]</sub>`, then the description. Message prose: heading, then `→ to · state` (parts dropped when unset), a blank line, the text.
- **Card `role`.** `AgentCard.role`, added to `_CARD_KEYS`; `card_to_dict` emits it only when non-empty so existing markers are byte-stable. The schema accepts any string; `ROLE_VALUES = ("author", "reviewer", "ci")` is enforced by the `join --role` argparse `choices`.
- **Login once per verb.** `room.py` gains `_login(gh, memo)` running `gh api user` and returning `login`, memoised in a dict the verb creates; a failure or empty login writes a `warning:` line and returns `""` (Q2). `_post_message(gh, repo, number, message, login="", role="")` forwards to `render_comment`. `message` and `close` find the role with the poster's card from `_read_room`'s `cards`; `watch` creates one memo for all its round-cap posts and `_cap_task` receives the card it already holds.
- **Rejoin states the role again.** `join` renders from the flags given, so a rejoin without `--role` clears the role (Q4).
- **Gate.** `_post_review` reads the login with `gh(["api", "user"])` once and builds the body `### ☕ shipd · semantic-review · reviewer (for @login)`, a newline, then `Semantic review: N inline comments. Full report in the summary comment.`, or `Semantic review posted. Full report in the summary comment.` when there are no inline comments (Q5). `ROOM_AGENT` supplies the name. Failure drops the `(for @login)` segment.
- **Callers.** `plugins/s/skills/room/SKILL.md` and `plugins/s/harness/bodies/room.md` tell the agent to pass `--role` when the user names one; `plugins/s/integrations/copilot/room-wake.yml` joins with `--role ci`.
- **Epic Decision relied on.** "Identity lives in the comment" in `pr-conversations`.
- **Version.** One patch above `main`'s `plugins/s/.claude-plugin/plugin.json` at build time.

Risk: existing tests assert the old prose and the fakes reject `gh api user`; the tasks update them. Risk: a login read costs one extra `gh` call per verb, accepted by the epic.

## Questions and answers

### Q1: Heading markup
- **Question:** Should the speaker heading render as (1) a level-3 markdown heading `### ☕ shipd · ...`; or (2) a bold line? Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) Level-3 heading. The epic calls it a visible heading and the pull request body already opens with a real heading; it stays readable beside the hidden marker.
- **Queued:** q-room-identity-heading-markup

### Q2: Missing role or failed login
- **Question:** When the card has no role or the login read fails, should the heading (1) drop the missing segment, warn on stderr for a failed login, and still post; or (2) fail the verb? Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) Drop the segment and post. A comment-level cosmetic gap must not block an agent's turn in the room.
- **Queued:** q-room-heading-missing-role-or-login

### Q3: Where a message's role comes from
- **Question:** Should `message` and `close` take the heading role from (1) the poster's own card; or (2) a `--role` flag on each verb? Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option 1. The role is the card's `role`, which `room join --role` sets; `message` and `close` get no `--role` flag. The oracle left the no-role fallback open; Q2 settles it as dropping the segment.
- **Cited:** epic/pr-conversations

### Q4: Role on a rejoin without the flag
- **Question:** Should a rejoin without `--role` (1) re-render from the flags given, clearing the role; or (2) keep the earlier card's role? Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) Clear it, as `--skill` and `--description` already behave; it keeps `join` stateless and the skill passes `--role` each time.
- **Queued:** q-room-rejoin-without-role
- **Relied on by:** room-threaded-findings

### Q5: Shape of the branded review submission body
- **Question:** Should the body be (1) the heading plus one pointer sentence; or (2) the heading alone? Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) Heading plus `Semantic review: N inline comments. Full report in the summary comment.`; a reader of the review list still learns where the report is.
- **Queued:** q-review-submission-body-shape

## Readiness attestation

### Problem and motivation

Agent comments on PR 14 were indistinguishable, and the epic requires a heading naming agent, role, and person.

Evidence:

- https://github.com/mikkel-bergmann/unkannybanny/pull/14 showed four comments under one account.
- `plugins/s/skills/room/scripts/room_schema.py` `_card_prose` and `_message_prose` render no role or login.
- `plugins/s/skills/review/scripts/review_gate.py:849` holds the one-line submission body.

### Scope and non-goals

The change touches the two renderers, the verbs that post, the join flag, and the gate's submission body only.

Evidence:

- In scope: `room_schema.py`, `room.py`, `review_gate.py`, tests, skill text, wake yml, doc, version.
- Out of scope: join's edit target (`room-join-owns-its-card`), summary and inline comments.

### Affected capabilities and files

Two capabilities: `pr-room` and `semantic-review`.

Evidence:

- `pr-room`: `room-agent-card` (base bf3ca2d13969) and `room-message-shape` (base e6ee47d60d96), from `spec_status.py base-hash`; new `room-join-role`, `room-poster-identity`. `semantic-review`: new `gate-review-submission-body`; `gate-poster` is left unmodified.
- Files: `plugins/s/skills/room/scripts/room_schema.py`, `plugins/s/skills/room/scripts/room.py`, `plugins/s/skills/review/scripts/review_gate.py`, `plugins/s/skills/room/tests/test_room_schema.py`, `plugins/s/skills/room/tests/test_room.py`, `plugins/s/skills/review/tests/test_review_gate.py`, `plugins/s/skills/room/SKILL.md`, `plugins/s/harness/bodies/room.md`, `plugins/s/integrations/copilot/room-wake.yml`, `docs/pr-room.md`, `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `spec_status.py base-hash pr-room room-agent-card` printed `bf3ca2d13969`, exit 0; the room and review test fakes raise on an unknown `gh api` read, observed in `test_room.py` FakeGh.

### No open task-shaping decision

Every task-shaping decision is settled.

Evidence:

- Message role source: settled by the oracle, Q3.
- Heading markup, missing segments, rejoin, submission body: settled by planner defaults, Q1, Q2, Q4, Q5.
- Heading text and login source: settled by the epic Decisions.
