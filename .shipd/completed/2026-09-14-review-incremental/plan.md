# review-incremental
Status: verified
Epic: review-rubric

## Idea

Stop the gate re-reporting a finding the reviewer already pushed back on, by
giving each posted finding a stable identity and reading prior dispositions
back before the next review reports.

### Motivation

The epic's Introduction names the defect: "The gate re-reviews every push in
full, so a finding the author already dismissed returns identically." A posted
inline body carries no identity, so nothing connects a finding on one head to
the same finding on the next, and a reasoned push-back has to be repeated after
every push.

### Details

- Embed a hidden identity marker in each inline body `post` renders, hashed
  from the finding's path and its normalized `what` text.
- Add `review_gate.py prior <pr>`, emitting each gate thread's identity,
  severity, what-text, and how it was dispositioned.
- Teach the skill to read that back before reporting and drop a finding whose
  identity matches a thread a reviewer answered with a reasoned reply.
- State the trigger in the References table's existing posting row, which costs
  no new line.

Affected capabilities: `semantic-review` (one added requirement).
Impact: `plugins/s/skills/review/scripts/review_gate.py`,
`plugins/s/skills/review/SKILL.md`,
`plugins/s/skills/review/references/posting.md`,
`plugins/s/skills/review/tests/test_review_gate.py`, and
`plugins/s/.claude-plugin/plugin.json`. No new dependencies, and no change to
`semdiff.py`.

### Non-goals

- No local cache. The pull request's own threads are the only store, so a
  pre-push review stays stateless.
- No fuzzy matching. A reworded finding hashes differently and is reported
  again; silently swallowing a near-miss is worse than one repeat.
- No suppression of a finding a commit dispositioned. That evidence means it
  was implemented, so a recurrence is a regression.
- No change to `post`'s filtering behaviour. It keeps rendering every finding
  it is handed.
- No change to the `resolve`, `autoreply`, or `protect` verbs.

## Implementation

- **Identity is the path plus the normalized `what`, never a line number.**
  The marker is `<!-- shipd-finding <hash> -->` where `<hash>` is the first
  twelve hex characters of the SHA-256 of `"<path>\n<normalized what>"`.
  Normalization lowercases and collapses whitespace runs to a single space.
  Line numbers are excluded deliberately: a finding's line moves as the diff
  around it changes, so an anchor-based identity would miss the recurrence it
  exists to catch. Rejected: a random id per finding, which cannot match across
  two independent reviews because nothing derives it from the finding itself.

- **The marker goes last in the body, never first.** `parse_severity` matches
  the severity marker against the body's lstripped opening, so anything
  prepended breaks every severity readback. Appending leaves that parser, and
  the visible rendering, untouched.

- **`prior` reports the evidence class; it never decides.** The verb emits one
  entry per gate-authored thread — `hash`, `severity`, `what`, `thread_id`,
  `resolved`, and a `disposition` of `replied`, `autoreplied`, `commit-only`,
  or `none`. The skill applies the suppression rule. This follows the seam the
  oracle identified: `autoreply` is already a separate verb that parses the
  gate's own body format mechanically and leaves what it cannot parse to
  judgement. Rejected: filtering inside `post`, which would silently drop a
  finding the skill still believes in.

- **Only `replied` suppresses, and the two canonical bodies are excluded.**
  `resolve` today accepts either a reply or a commit landed after the thread
  was created. That commit rule is purely time-based, so it proves nothing
  about implementation and must never suppress — a recurrence after a real fix
  is a regression, which is the most valuable finding the gate can produce.
  `autoreply`'s two canonical texts in `AUTOREPLY_DISPOSITIONS` are matched
  exactly and classified `autoreplied`, because a finding nobody assessed is
  not a finding anybody dismissed.

- **The query must learn `path`.** `_THREADS_QUERY` fetches `id`,
  `isResolved`, and each comment's `databaseId`, `author`, `createdAt` and
  `body`, but no `path`. The verb needs the thread's `path` to report an entry
  a reader can locate, so the query gains that field. The hash itself comes
  from the marker in the body, so `path` is for reporting rather than matching.

- **The trigger costs no line, because there is none to spend.** `SKILL.md`
  stands at 299 against `assertLess(len(lines), 300)` — zero headroom. There is
  also no inline posting step to extend: the workflow runs steps 1 to 7 and
  posting lives wholly in `references/posting.md`. So the trigger extends the
  existing References row at `SKILL.md:46`, a single table line whose `Load
  when` cell grows without adding a line. Extending that cell only adds words,
  so the agreement test's shared-word count cannot fall. The detail — the verb,
  the evidence classes, and the suppression rule — lands in `posting.md`, which
  the row already points at.

- **Suppression is stated in the report, never silent.** A review that dropped
  findings says how many and names the pull request they were answered on. A
  reviewer who cannot see what was withheld cannot tell a working suppression
  from a broken one.

- **Risk: a suppressed finding that should have recurred.** The conservative
  choices all point the same way — exact hash only, reply-only evidence,
  canonical autoreplies excluded, commit evidence ignored. Each errs toward
  reporting twice rather than staying silent once.

- **Version bump.** `plugins/s/.claude-plugin/plugin.json` moves to `0.6.219`,
  per the cache-snapshot rule in AGENTS.md. `review_gate.py` is not in the
  copilot install set, so no gate install goes stale from this change.

## Questions and answers

### Q1: Where should a previously-dismissed finding be suppressed?

- **Question:** For incremental review, should a previously-dismissed finding be suppressed in a readback verb the `/s:review` skill consumes and acts on, or mechanically inside `review_gate.py post`? Options: a new `prior` verb emitting prior dispositioned findings as JSON, with the skill omitting matches itself; or `post` reading the threads back and dropping matches so suppression cannot be forgotten. Recommended: the readback verb.
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Add the readback verb and let the skill match and suppress before it reports; do not fold identity matching into `post`. The hidden per-finding marker still belongs in the inline body `post` renders, since that is what the verb reads back, but the decision to drop a finding stays a judgement the skill makes and states. The epic's Design already places the match "before reporting", in the review rather than the poster, so `post` keeps its no-analysis posture. The existing `autoreply` verb is the precedent for the shape: a separate verb parsing the gate's own inline-body format mechanically, with anything it cannot parse left for judgement.
- **Cited:** `epic/review-rubric` — "Incremental review consumes that readback: before reporting, the review matches its findings against the threads already posted, and suppresses a match a human dismissed."; `plugins/s/skills/review/references/posting.md` — "It performs no analysis of its own — all judgement stays in this skill; the engine only enforces that each finding was implemented or answered before its thread resolves."

### Q2: How should the last member get room under the line ceiling?

- **Question:** `SKILL.md` stands at 299 lines against a spec-enforced 300-line ceiling, and this member needs a workflow trigger a reviewer reads on every review. Options: fold the trigger into an existing step so no new inline lines are spent; raise the ceiling through an epic amendment stating why a larger body is right; or put the trigger behind a reference with no inline line at all. Recommended: fold into an existing step.
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Fold it into what is already there. The reference-only option is forbidden outright by the verified requirement that guidance running on every review stays inline in `SKILL.md`, and raising the ceiling is an explicit non-default needing its own amendment arguing the body is the wrong shape, which nothing about this member supports. Extending what exists spends no new inline lines, keeps the whole trigger where the reader meets it, and leaves the ceiling intact. Incremental review is a gate-mode condition, which is consistent with attaching it to the posting surface rather than opening a new top-level step.
- **Cited:** `verified/semantic-review` — "Guidance that runs on every review SHALL stay inline in `SKILL.md` ... `SKILL.md` SHALL stay under 300 lines."; `epic/review-rubric` — "A member needing room moves guidance into a reference file rather than raising the number ... Raising it is possible but never incidental: it takes its own amendment stating why the larger body is the right shape."
