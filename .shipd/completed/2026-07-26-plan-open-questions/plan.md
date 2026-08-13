# plan-open-questions
Status: verified

## Idea

When investigation surfaces a question only the user can settle, the digest
currently buries it in prose (a live session wrote "One thing to settle in
planning (not now): …" mid-digest, easy to scroll past). The user wants such
questions explicit and scannable: a dedicated **OPEN QUESTIONS** header
listing them — displayed at the checkpoint, not asked there — so the user can
address them in the typed go-ahead reply or knowingly defer them to the
post-gate rounds.

### Non-goals

- No change to the no-questions rule of the investigation turn: open
  questions are listed, never posed as a dialog or answered-by-default
  there.
- No change to the go-ahead prompt's two options, the digest's other
  content, the depth gate, or the grill loop.

Affected capabilities: `shipd-plan` (modified — `investigation-findings-digest`).
Impact: `plugins/s/skills/plan/SKILL.md`,
`plugins/s/.claude-plugin/plugin.json`.

## Implementation

- **An OPEN QUESTIONS section closes the digest.** When investigation leaves
  one or more genuinely open task-shaping questions, the digest lists them
  under an `OPEN QUESTIONS` header as its final section, immediately before
  the go-ahead prompt. Displayed, not asked: the skill does not pose them in
  the investigation turn; the user may answer any of them in the typed
  go-ahead reply, and whatever stays open is settled in the post-gate
  decision rounds. When no such question exists, the header is omitted —
  never an empty section.
- **Version bump to 0.3.1** in `plugins/s/.claude-plugin/plugin.json`, same
  PR, per the cache-snapshot rule in AGENTS.md.

Risks: none structural — a formatting/contract refinement of the existing
digest. Eval note: the plan eval cases still fail structurally against the
checkpoint (the harness cannot answer the typed go-ahead; documented in PR
#31), so no eval signal is available for this SKILL.md change until the
runner learns to reply.
