# brand-subtle
Status: verified
Planned-at: 0545cd1ad65e4f1a918b266110f71e73e7548c02
Gated-hash: f9b806bd2b7a

## Idea

Quiet the shipd brand: headings, titles, and commit subjects show only the ☕
mark, a `<sub>☕ Posted by Shipd</sub>` footer names shipd instead, and the
review gate keeps the brand word.

### Motivation

People reading a shipd pull request (for example
https://github.com/mikkel-bergmann/unkannybanny/pull/18) see `☕ Shipd: ` in
the title, `☕ Shipd Pull Request` in the body, and `☕ shipd ·` on every
room comment, and the user finds that too loud. They cannot get a quieter
brand today, because the prefix and headings are fixed in the engine.

### Details

- `spec_common.BRAND_PREFIX` becomes `☕ `. `brand_subject` treats any subject
  starting with `☕` as branded, so `☕ Shipd: ` subjects, `☕ ` subjects, and
  `☕` without a space are never branded twice. The commit-msg hook,
  `wiki_autocommit`, `brand.py subject`, and `pr_title.py` pick it up through
  the constant.
- The `/s:pr` body heading becomes `## ☕ Pull Request`, and the body ends
  with a `<sub>☕ Posted by Shipd</sub>` paragraph directly before the
  generated-by line.
- PR-room agent Messages head with `### ☕ <agent>[ · <role>][ (for @<login>)]`
  and end with the `<sub>☕ Posted by Shipd</sub>` footer after a blank line.
  Agent Cards become one line, `<sub>☕ **<name>** joined the room …</sub>`.
- The review gate keeps its brand word: the summary's
  `**☕ shipd** semantic review` line and the review submission's
  `### ☕ shipd · semantic-review · reviewer (for @<login>)` heading stay.
- Docs, skill text, harness bodies, AGENTS.md, and README text that quote the
  old strings are updated.

Affected capabilities: `shipd-brand`, `shipd-pr`, `pr-room` (modified);
`semantic-review` unchanged. Impact: `spec_common.py`, `room_schema.py`,
`room.py`, `review_gate.py`, the pr skill and harness pr files, docs, tests.

### Non-goals

- No change to the review gate's summary or submission text (user decision 4).
- No rewrite of existing commit subjects or pull request titles already
  published with `☕ Shipd: `.
- No edit to `.shipd/completed/` archives or to the completed
  `pr-conversations` epic, which keep the old strings as history.
- No footer on Agent Cards or `user` messages, and no configurable brand.

## Implementation

- **Prefix.** `BRAND_PREFIX = "☕ "` in `spec_common.py`. `brand_subject`
  returns the subject unchanged when it starts with `"☕"` (that one test
  covers `☕ `, `☕` with no space, and the legacy `☕ Shipd: `), keeping the
  empty and autosquash rules. Rejected: listing each legacy prefix separately,
  which is redundant with the single `☕` test.
- **Speaker heading.** `room_schema.speaker_heading(agent, role="", login="",
  brand=False)`: by default it returns `☕ <agent>[ · role][ (for @login)]`;
  with `brand=True` it returns `☕ shipd · <agent>…` exactly as today.
  `review_gate._post_review` calls it with `brand=True`, so the review
  submission body is byte-identical (decision 4). Rejected: a hand-spelled
  heading in `review_gate.py`, which would spell the heading in two places.
- **Footer.** `room_schema.FOOTER = "<sub>☕ Posted by Shipd</sub>"`.
  `_message_prose` for an agent Message returns
  `<heading lines>\n\n<text>\n\n<FOOTER>`; a `user` Message stays `text`
  alone. Parsing is untouched: `text` comes from the marker's parts, so
  neither heading nor footer enters it.
- **Card.** `_card_prose(card)` returns
  `<sub>☕ **<name>** joined the room[ from <harness>][ · skills: a, b]</sub>`
  plus `\n\n<description>` when set; no heading, role, login, or footer (Q1,
  Q2). `render_comment` keeps its `login` and `role` parameters for Messages
  and ignores them for a card. `room.py cmd_join` renders the card without a
  login and no longer calls `_login` (the card shows none).
- **PR body.** The pr skill, `harness/bodies/pr.md`, and
  `harness/references/pr.md` name `## ☕ Pull Request` as line 1 and the
  `<sub>☕ Posted by Shipd</sub>` paragraph directly before the last line,
  the generated-by line. `docs_lint.py` accepts that body (verified).
- **Docs.** Replace old strings in `README.md` (the `/s:pr` table row),
  `AGENTS.md` (the store-amend subject becomes `☕ shipd: amend epic <slug>`,
  carrying the `☕ ` brand), `.shipd/README.md` (titles and commits start with
  `☕ `), `plugins/s/skills/build/SKILL.md` (Phase 6 `/s:pr` sentence), and
  `docs/pr-room.md` (agent comments open with `☕ agent · role (for @login)`
  and end with the footer). Keep each edited prose line within 80 columns.
- **Version.** `plugins/s/.claude-plugin/plugin.json` moves one patch above
  `git show origin/main:plugins/s/.claude-plugin/plugin.json`, read right
  before committing.

Risk: a test elsewhere hardcodes `☕ Shipd: ` or `☕ shipd ·`; the tasks list
every known site, and the build, pr, room, and review suites are run whole.

## Questions and answers

### Q1: Does the one-line card keep role and login?
- **Question:** Should the one-line Agent Card keep the role and login
  segments? Options: (1) keep them in heading order; (2) drop them from the
  prose, the marker still carrying `role`. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 2. The user's decision 3 gives the card's exact shape,
  `<sub>☕ **<name>** joined the room …</sub>`, with the trailing harness and
  skills segments only; role stays in the marker and in `room list`.
- **Queued:** q-pr-room-one-line-card-role-login

### Q2: Do Agent Cards carry the footer?
- **Question:** Should Agent Card comments also end with
  `<sub>☕ Posted by Shipd</sub>`? Options: (1) no, agent Messages only;
  (2) yes. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The user's decision 3 scopes the footer to agent
  messages; the card is a single `<sub>` line already.
- **Queued:** q-agent-card-brand-footer

## Readiness attestation

### Problem and motivation

The brand reads too loud on pull requests, and the user asked for the word
`Shipd` to leave headings and titles while a footer names shipd.

Evidence:

- `plugins/s/skills/build/scripts/spec_common.py:1152` spells
  `BRAND_PREFIX = "☕ Shipd: "`.
- `plugins/s/skills/room/scripts/room_schema.py:128` renders `☕ shipd ·`
  headings; `plugins/s/skills/pr/SKILL.md:42` fixes `## ☕ Shipd Pull Request`.
- The user's request and decisions 1–4, given while viewing
  https://github.com/mikkel-bergmann/unkannybanny/pull/18.

### Scope and non-goals

Three capabilities change; the review gate's text, archived changes, and
published subjects stay as they are.

Evidence:

- In scope: capabilities `shipd-brand`, `shipd-pr`, `pr-room`.
- Out of scope: `semantic-review` requirements `gate-review-submission-body`
  and the brand line at `plugins/s/skills/review/scripts/review_gate.py:74`.
- Out of scope: `.shipd/completed/` (constitution: completed changes are
  immutable) and `.shipd/epics/pr-conversations/epic.md`.

### Affected capabilities and files

Ten requirements across three capabilities and about twenty files change,
because the prefix, the room renderer, and the PR body shape are each quoted
in code, tests, and docs.

Evidence:

- `shipd-brand`: `brand-subject-helper` (base b3dc3575e7d0),
  `brand-script-verbs` (c5af0b66114a), `commit-brand-hook-install`
  (4b3d514361ef), `brand-engine-commits` (e3b6d8074f8d).
- `shipd-pr`: `pr-skill-writes` (584516de8bfa), `pr-title-render`
  (ff7709723c94).
- `pr-room`: `room-agent-card` (8f621416aa54), `room-message-shape`
  (09d9ea1ff1ed), `room-join-role` (3720116b456c), `room-poster-identity`
  (c60d37d25d98). Hashes from `spec_status.py base-hash`.
- Code: `spec_common.py:1152-1169`, `room_schema.py:128-136,187-197,324-334`,
  `room.py:562`, `review_gate.py:891`.
- Runnable premise: `brand.py subject "x"` printed `☕ Shipd: x`;
  `pr_title.py title --summary "☕ Add x"` printed `☕ Shipd: ☕ Add x`, so
  today's idempotence test misses a bare `☕ ` prefix.
- Runnable premise: `docs_lint.py` on a staged body with `## ☕ Pull Request`
  and a `<sub>☕ Posted by Shipd</sub>` paragraph before the generated-by line
  exited 0.

### No open task-shaping decision

Every decision is settled: the prefix, PR body, room heading and footer, and
review gate text by the user; the card shape and card footer by the user's
decision 3 (Q1, Q2); the rest by investigation.

Evidence:

- Prefix, body heading and footer, room heading and footer, review brand
  kept: user decisions 1–4.
- Card role and login dropped: Q1, answered by the user's decision 3.
- No footer on cards: Q2, answered by the user's decision 3.
- `join` stops reading the login, and `speaker_heading` gains `brand=True`
  for the review gate: settled by investigation of `room.py:562` and
  `review_gate.py:891`.
