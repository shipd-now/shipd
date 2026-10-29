# drop-question-rejection-recovery
Status: verified
Planned-at: 099c1c38fbd43ac971624461339b301e202f3b50
Gated-hash: 2a9acee28a5a

## Idea

Remove the question rejection recovery rule from every skill, harness body,
and spec, because the harness bug it worked around no longer exists.

### Motivation

Seventeen skills spend a section on a harness bug that delivered a question
dialog as a tool rejection; the user reports that bug belonged to an older
harness version. Every session still loads that dead workaround, and every new
interactive skill is required by spec to copy it.

### Details

- Delete the rule from 17 SKILL.md files: a `## Question rejection recovery`
  section in 13, a `### Question rejection recovery` subsection in `build`,
  and a list item in `epic-grill`, `onboard`, and `plan-deep`.
- Delete the "rejected or interrupted dialog" sentences from the harness
  bodies `ask.md`, `forget.md`, `plan-deep.md`, `status.md`, and the
  reference `harness/references/forget.md`.
- Reword the two `remember` SKILL.md sentences that cite the
  "question-rejection-recovery roster".
- Remove requirement `question-rejection-recovery`; drop the rule from the
  `doctor`, `gate`, `forget`, and `remember` requirements.
- Add a guard test so the rule does not come back.
- Bump the plugin version.

Affected capabilities: `shipd-interaction` (one removed, one added),
`shipd-doctor`, `shipd-gate`, `shipd-memory` (modified). Impact: markdown
under `plugins/s/`, one new test, `plugin.json`.

### Non-goals

- The AskUserQuestion dialogs themselves stay; only the rejection workaround
  goes.
- The `dialog-prose-separation` and `question-brief` requirements are
  untouched.
- Archived changes under `.shipd/completed/` keep their history.

## Implementation

- **SKILL.md sections.** Delete each section from its heading through the
  line before the next heading, including the heading and the blank line
  after the section, so no empty section or double blank line is left. For
  the list items in `epic-grill`, `onboard`, and `plan-deep`, delete the whole
  `- **Question rejection recovery.** …` or `4. **Question rejection
  recovery.** …` item and its continuation lines.
- **Harness bodies.** Delete only the sentence that starts "Never treat a
  rejected or interrupted dialog" (`ask.md`, `forget.md`, `status.md`) or
  "If a dialog is rejected" (`plan-deep.md`), and rewrap the remaining
  paragraph to the file's width. In `harness/references/forget.md`, delete
  the paragraph "An interaction that comes back rejected or interrupted is
  **not** a decline: …" and its following blank line.
- **remember SKILL.md.** At line 178, replace "this skill's confirmation is a
  typed round, so it does not join the question-rejection-recovery roster."
  with "this skill's confirmation is a typed round." At line 300, replace
  "— which keeps `/s:remember` off the question-rejection-recovery roster."
  with a full stop after the bold sentence. Rewrap the touched paragraphs.
- **Guard test.** Add `plugins/s/skills/build/tests/test_no_rejection_recovery.py`.
  It scans every `*.md` under `plugins/s/skills/` and `plugins/s/harness/`
  for the case-insensitive phrases `rejection recovery`,
  `rejection-recovery`, and `rejected or interrupted`, and fails naming each
  `path:line`. Model it on `test_harness_neutral_prose.py`.
- Rejected: keeping a one-line neutral version of the rule. The user said the
  bug is gone, so the guidance has no remaining trigger.

Risk: a missed copy. The guard test catches every phrasing the repo uses
today.

## Readiness attestation

### Problem and motivation

A workaround for a fixed harness bug is loaded by 17 skills and required by
four specs.

Evidence:

- The user stated the bug belonged to an older harness version.
- `.shipd/verified/shipd-interaction/spec.md:3` requires the rule in every
  interactive skill.

### Scope and non-goals

The change removes the rule's text and its spec requirements; dialogs stay.

Evidence:

- In scope: the 17 SKILL.md files and the five harness files listed above.
- Out of scope: `dialog-prose-separation` and `question-brief` in
  `.shipd/verified/shipd-interaction/spec.md`.

### Affected capabilities and files

Four capabilities and 24 files change, plus one new test.

Evidence:

- `shipd-interaction`: `question-rejection-recovery` (base 248928f65574).
- `shipd-doctor`: `doctor-skill-registration` (base 4ad72b74fd95).
- `shipd-gate`: `gate-skill-registration` (base 13f3972f23d6).
- `shipd-memory`: `forget-skill` (base 0f52cf49fc6e), `git-backing-flow`
  (base 16368954b51c), `remember-skill` (base 498024c712b0).
- Skills with the rule: autopilot, build, doctor, epic, epic-grill, fix,
  forget, gate, initiative, onboard, plan, plan-deep, prd, research, review,
  status, worktree-hooks.
- A grep of `plugins/s/skills/*/tests` for "re-offer" and "rejection
  recovery" returns no matches, so no existing test pins the rule.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Remove the whole rule rather than only the bug sentence: settled by the
  user's statement that the bug is no longer relevant.
- Guard test: settled by the workspace wiki,
  `[[prompt-convention-enforcement]]`.
