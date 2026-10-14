# question-brief
Status: ready
Theme: developer-experience

## Idea

Give every shipd question a short brief: what the decision is about, why it
matters, a small example, and the options with the recommended one first.
One shared reference defines the brief, and every skill that asks points to
it.

### Motivation

A user answering a shipd question often cannot tell what it is about. The
`/s:epic-grill` final round showed "room-cli-verb Q2 — default `--state` for
a `--task` reply when omitted?" with no word on what the feature does or
what each option changes. A question the user cannot understand gets a
guessed answer, and the guess lands in the spec.

### Details

- A new reference, `plugins/s/skills/document/references/question-brief.md`,
  defines the brief, where it goes, and four worked examples.
- Every SKILL.md that mentions `AskUserQuestion` points to it, and so does
  that skill's harness body.
- A multi-question dialog becomes a typed round. A dialog stays only for one
  self-contained question whose brief fits in its question text and option
  descriptions.
- A new contract test checks the pointer in every asking skill and body.

Affected capabilities: `shipd-interaction` (one requirement modified, one
added) and `shipd-epic-grill` (one requirement modified).

### Non-goals

- No engine, linter, or gate code change.
- No change to what any skill asks, only to how it presents the question.
- No rewording of the question rejection recovery paragraphs.

## Implementation

- **The brief, four parts in order** (user, Q1):
  1. **The decision**, as a bold heading in plain words, followed by the
     member and `Q<n>` in brackets where the skill tracks them.
  2. **Why it matters**: one or two sentences on what the feature does and
     what the answer changes.
  3. **An example**: one concrete command, input, or scenario. Leave it out
     only when the decision has no concrete instance.
  4. **The options**, lettered, recommended first and marked
     "(recommended)", each with what choosing it causes.
- **Placement** (user, Q2): use a plain-text numbered typed round, answered
  like "1a 2b", whenever a round has more than one question or any brief
  runs past one line. Use an AskUserQuestion dialog only for one
  self-contained question; its brief rides in the question text and option
  descriptions, and the turn carries no other prose.
- **The reference file.** First line `<!-- doc-type: reference -->`; title
  "The shipd question brief"; sections: "The four parts", "Where the brief
  goes", "Worked examples", "A bad question". It must pass
  `plugins/s/skills/document/scripts/docs_lint.py` and stay under the
  250-line reference cap.
- **Worked examples** (approved by the user, copy them into the reference
  with these contents):
  - *epic-grill typed round.* Before: "room-cli-verb Q2 — default `--state`
    for a `--task` reply when omitted?". After: heading "Reply state when
    `--state` is left out (room-cli-verb, Q2)"; why: "`shipd room message
    --task <id>` posts an agent's reply on a PR task. Each reply carries a
    state that tells the room whose turn it is. This decides the state when
    the caller omits it."; example: "`shipd room message --task t1 --to
    alice "Does this cover retries?"` hands the turn to alice."; options:
    a) "Use `input-required` with `--to`, otherwise `working`
    (recommended). A reply addressed to someone hands them the turn."
    b) "Require `--state`. Every caller must name it; a missing flag exits
    with a usage error."
  - *epic scoping typed round.* Before: "Include the GitHub Action wake-up
    in this epic?". After: heading "Scope: the automatic wake-up"; why:
    "The epic lets agents talk over PR comments. Without a wake-up, an
    agent sees a comment only when someone runs `room watch`. With one, a
    GitHub Action starts the agent when a comment arrives."; example:
    "alice comments "@claude retry this" and the agent answers within a
    minute, with nobody at a terminal."; options: a) "Plan it as its own
    member (recommended). It ships after the core verbs and can be cut
    alone." b) "Leave it out. Record it under Out of scope for a later
    epic."
  - *forget confirm dialog.* Before: "Remove memory-diagram-style?".
    After, question text: "Remove memory-diagram-style? It tells /s:plan to
    draw Mermaid flowcharts, not ASCII. After removal, plans fall back to
    the default style."; options "Keep it (Recommended)" and "Remove it:
    deletes the page and its index entry".
  - *workspace sync dialog.* Before: "How should sync handle members?".
    After, question text: "3 of 5 member repos are missing here, and 2
    already have local checkouts. Sync can reuse them or clone fresh
    copies."; options "Reuse what I have (Recommended): maps the 2 and
    clones only the 3 missing", "Clone everything fresh: re-clones all 5
    into the workspace", "Review one by one".
- **The pointer.** Each asking SKILL.md gets one bolded paragraph, placed
  directly above its question rejection recovery paragraph (or above its
  question contract where it has no recovery paragraph):

  ```
  **Brief every question.** Open each question with the brief that
  `${CLAUDE_PLUGIN_ROOT}/skills/document/references/question-brief.md`
  defines, and follow its rule on dialogs and typed rounds.
  ```

  Each matching harness body gets the same sentence with the path written
  `skills/document/references/question-brief.md`, and never the token
  `AskUserQuestion`, `subagent`, or `sub-agent`.
- **The roster** is computed, not listed: every
  `plugins/s/skills/*/SKILL.md` containing `AskUserQuestion` (21 today), and
  `plugins/s/harness/bodies/<skill>.md` for each of those that exists.
- **Contract edits beyond the pointer.**
  - `/s:epic-grill`: the final round and the re-check's further round become
    numbered typed rounds with a brief per question; drop the four-question
    dialog limit and the "one dialog" wording. Its harness body already asks
    a typed round; add the brief.
  - `/s:epic` and `/s:initiative`: their "question contract
    (AskUserQuestion)" sections become typed rounds with a brief per
    question; rename the heading to "The question contract (typed round)".
  - `/s:workspace`: the `init` two-question dialog and the
    member-by-member review become typed rounds; the `sync` and `map`
    single-question dialogs stay, with the brief in the question text.
- **Test.** New `plugins/s/skills/build/tests/test_question_brief_contract.py`:
  computes the roster, asserts the reference exists with its doc-type
  marker and the four part names, and asserts each roster SKILL.md and body
  contains `skills/document/references/question-brief.md`.

Risk: a skill that later gains its first `AskUserQuestion` fails the test
until it adds the pointer. That is the intent.

## Questions and answers

### Q1: Approve the brief format?
- **Question:** Approve the four-part brief (decision, why it matters,
  example, options recommended first) as shown in the four worked examples,
  or change it? Recommendation: approve as shown.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Approved as shown.
- **Queued:** none

### Q2: Where do long briefs go?
- **Question:** Use a typed round whenever any brief runs past one line and
  keep a dialog only for one self-contained question; keep every dialog and
  squeeze the brief in; or drop dialogs everywhere? Recommendation: typed
  round if long.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Typed round when a round has more than one question or a
  brief runs past one line; a dialog only for one self-contained question.
- **Queued:** q-question-brief-dialog-placement

## Readiness attestation

### Problem and motivation

Skills ask questions without the context needed to answer them.

Evidence:

- `plugins/s/skills/epic-grill/SKILL.md:149-153` tells the grill to put all
  context inside dialog text, which produced the bare
  "room-cli-verb Q2" dialog the user could not answer.
- `plugins/s/skills/epic/SKILL.md:268-280`,
  `plugins/s/skills/initiative/SKILL.md:224-230`, and
  `plugins/s/skills/workspace/SKILL.md:111,557` ask multi-question dialogs
  with no brief rule.

### Scope and non-goals

Prose contracts, one reference, and one test; no engine code.

Evidence:

- `/s:plan` already briefs before asking
  (`plugins/s/skills/plan/SKILL.md:709-720`), so the pattern exists.
- No test checks shared question rules today: no test under
  `plugins/s/skills/build/tests/` mentions the rejection recovery rule.

### Affected capabilities and files

Two capabilities, 21 skills and their harness bodies, one new reference, one
new test.

Evidence:

- `shipd-interaction`: `dialog-prose-separation` (base 99ac8a4d334a), new
  `question-brief`; `shipd-epic-grill`: `epic-grill-final-round` (base
  3e15cd8dd303), from `spec_status.py base-hash`.
- Roster from `grep -l AskUserQuestion plugins/s/skills/*/SKILL.md`: ask,
  autopilot, build, demo, doctor, drive, epic-grill, epic, fix, forget,
  gate, initiative, onboard, plan, prd, remember, research, review, status,
  workspace, worktree-hooks. Each has a body under
  `plugins/s/harness/bodies/`.
- Harness bodies stay under the ceiling in
  `plugins/s/skills/build/tests/test_harness_bodies.py`; the longest,
  `review.md`, is 150 lines.
- `plugins/s/.claude-plugin/plugin.json` is at 0.6.283.

### No open task-shaping decision

Every task-shaping decision is settled.

Evidence:

- Brief format: user, Q1. Placement: user, Q2.
- Reference location: beside the documentation standard, which the user
  named as the writing guide.
- Harness bodies in scope: settled by investigation; they ask the same
  questions as their skills.
- Personal memory store: absent, so no preference applied.
