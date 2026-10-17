# room-polish
Status: verified
Planned-at: d04bc9a99d06021d1cfeaa15fdfc3513ea56b57a
Gated-hash: 24d4122b2c62

## Idea

Fix four rough edges the two-agent room test surfaced: a backgrounded
`watch`, a role-less `room list` card line, the review summary posing as a
room task, and a re-posted summary that forgets earlier verdicts.

### Motivation

Agents taking turns through `/s:room` on unkannybanny PR 16 had their
`watch` call backgrounded (breaking the foreground-only rule), could not see
each other's roles in `room list`, and saw a spurious `completed` task for
the review summary. Reviewers also lost the earlier "Fix required" verdict
once a re-posted review passed, so the PR no longer showed its history.

### Details

- `watch` timeout 600 → 540 seconds wherever the room skill names it, plus
  the rule that the tool call's own timeout must exceed 540 seconds.
- `room list` text card line shows `role <r>` and drops `harness` when unset.
- The summary comment carries only the gate's card, not a Message.
- A re-posted summary keeps an `Earlier reviews` `<details>` list.

Affected capabilities: `shipd-room` (room-skill-loop, room-skill-body),
`pr-room` (room-list-verb), `semantic-review` (gate-room-summary,
gate-finding-room-task, new summary-earlier-reviews). Impact:
`plugins/s/skills/room/SKILL.md`, `plugins/s/harness/bodies/room.md`,
`plugins/s/harness/references/room.md`, `docs/pr-room.md`,
`plugins/s/skills/room/scripts/room.py`,
`plugins/s/skills/review/scripts/review_gate.py`, their tests, and the plugin
version.

### Non-goals

- No change to `room.py watch`'s own `--timeout` default or the pr-room
  engine scenario that runs `watch 7 --timeout 600`.
- No task-view filter in `room.py` for legacy summaries already carrying a
  Message; the next re-post rewrites them.
- No change to the Actions Copilot gate workflow's own summary body.
- No cap on the length of the earlier-reviews list.

## Implementation

- **Timeout 540, tool timeout above it.** Every room-skill surface that
  names `--timeout 600` for the watch wait names `--timeout 540` instead:
  `plugins/s/skills/room/SKILL.md` (steps 3 and the `stay` stop),
  `plugins/s/harness/bodies/room.md` step 3, the reference's watch-output
  section, `docs/pr-room.md` (step 3 example and the stay section). SKILL.md
  says "nine-minute timeout" where it said "ten-minute". Each surface adds
  one sentence that the tool call running `watch` must carry its own timeout
  above 540 seconds; SKILL.md and `docs/pr-room.md` add "(on Claude Code, a
  Bash `timeout` of `600000` ms)". Rejected: keeping 600 and raising the tool
  timeout — 600000 ms is the Bash tool's maximum, so 600 can never be beaten.
- **Card line.** `room.py` `_card_line(card)` builds space-pair-separated
  parts: `card.name`, then `role <r>` only when `card.role`, then
  `harness <h>` only when `card.harness`, then `skills <csv|->`, then
  `version <v|->`, joined by two spaces. JSON output is unchanged.
- **Summary is not a task (Q1).** `render_summary` emits the gate's card
  marker line only; `_room_summary_line` and `render_summary`'s
  `status_state` parameter are deleted, and `post` stops passing
  `status_state=`. No code reads the Message's `verdict`/`status`, the card
  stays discoverable through `_parse_room`, and the summary's creation no
  longer matches the room-wake prefilter `<!-- shipd-room `. Rejected: a
  task-view filter on summary-marked comments in `room.py` — a second rule
  to keep in sync for a Message nobody reads.
- **Head record.** `render_summary(..., head=None, earlier=None)`. Given
  `head`, a hidden line `<!-- shipd-semantic-review-head <full sha> -->`
  (module constant `HEAD_MARKER_FMT`) is emitted. Tail order: fast-pass
  line, then (when `earlier` is non-empty) `""`,
  `<details><summary>Earlier reviews</summary>`, `""`, the entries, `""`,
  `</details>`, then (when head or room is given) `""`, head line, card
  line, then `""` and the footer. Without `head`, `earlier`, and `room` the
  body is byte-identical to today's.
- **Earlier entries.** New pure `earlier_reviews(previous)` takes the
  pre-existing summary comment dict (or `None` → `[]`) and returns entry
  lines newest first: first a line for the previous summary,
  `- <verdict> — `<sha7>` — <YYYY-MM-DD HH:MM> UTC`, where `<verdict>` is
  the text after `## Findings: ` on its first such line (`verdict unknown`
  when absent), `<sha7>` the first 7 characters of its head marker's sha
  (`unknown` when absent), and the time the comment's `updated_at`, else
  `created_at`, reformatted from `YYYY-MM-DDTHH:MM:SSZ` (the time segment
  dropped when neither is present, printed verbatim when unparseable); then
  every `- ` line inside the previous body's Earlier-reviews block, in
  order. Time comes from GitHub's own stamp, so `post` needs no clock.
- **Post wiring.** New `_find_summary(gh, repo, number)` returns the
  existing marker comment dict or `None` (the lookup `_upsert_summary`
  already does, which now calls it). `post` calls it once before the first
  upsert, computes `earlier = earlier_reviews(previous)`, and passes
  `head=sha, earlier=earlier` to all three `render_summary` calls, so the
  in-run fold and fast-pass re-upserts never record the run's own body.
- **Tests.** `test_review_gate.py`: FakeGh stamps `updated_at` on every
  comment POST and PATCH from an incrementing fixed clock; RoomSummaryTest
  and RoomPostTest move to card-only; new tests cover earlier entries.
  a review test feeds a posted summary and its inline comments to
  `room._parse_room`. `test_room.py` covers the card line.
  `test_room_skill.py` asserts `--timeout 540` and no `--timeout 600`.

Risk: an old summary without a head line yields sha `unknown` once; later
entries carry real shas.

## Questions and answers

### Q1: How does the summary stop being a room task?
- **Question:** The summary carries the gate's card and a completed Message,
  so it lists as a task. Options: (1) drop the Message, card only; (2) keep
  it and have `room.py`'s task view skip summary-marked comments.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** The user decided the summary must not appear as a task in
  `room list` or `watch`, the gate's card must stay discoverable, and the
  cleanest way is to be found by investigation. Investigation settles it as
  option 1: nothing reads the Message, and dropping it needs no room-side rule.
- **Queued:** q-gate-summary-room-task-visibility

### Q2: What does a role-less card line show?
- **Question:** The card line gains the role. With no role set: (1) omit the
  segment; (2) print `role -`. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** The user decided the card line shows the role and omits
  `harness` when unset; the same omit-when-unset rule applies to an unset
  role, matching the task line's `skill <s>` when set — option 1.
- **Queued:** none

## Readiness attestation

### Problem and motivation

Four defects from the two-agent room test block agents and reviewers in a PR
room.

Evidence:

- `plugins/s/skills/room/SKILL.md:64` names `--timeout 600`.
- `plugins/s/skills/room/scripts/room.py:585-588` `_card_line` omits role.
- `plugins/s/skills/review/scripts/review_gate.py:432-434,687-703` writes the
  summary Message; `_upsert_summary` (770-790) PATCHes the body in place.

### Scope and non-goals

The room skill surfaces, `room.py`'s card line, and `review_gate.py`'s
summary render and post change; engine watch defaults and the Actions
workflow do not.

Evidence:

- In scope: the files listed under Details.
- Out of scope: `plugins/s/integrations/copilot/copilot-review-gate.yml`,
  `.shipd/verified/pr-room/spec.md:663` (engine scenario).

### Affected capabilities and files

Three capabilities and eight files plus tests are affected.

Evidence:

- `shipd-room` room-skill-loop (base 5dc2e214af13), room-skill-body (base
  cd149a1fd79c); `pr-room` room-list-verb (base c5d1ed690e7f);
  `semantic-review` gate-room-summary (base dcfa49297dfe),
  gate-finding-room-task (base 98c1c7de0366).
- Runnable premise: `render_summary(pass review, room=...)` then
  `room_schema.build_tasks` returned one `completed` Task opened by
  `semantic-review` — the spurious task.
- Runnable premise: `room._card_line(AgentCard(name="claude-b",
  role="author"))` printed `claude-b  harness -  skills -  version -`.

### No open task-shaping decision

Every decision is settled.

Evidence:

- Timeout value 540 and the tool-timeout rule: user.
- Card line role display: user, Q2.
- Summary as card only: user plus investigation, Q1.
- Earlier-reviews list shape: user; time source (`updated_at`) and head
  record (hidden marker): investigation.
