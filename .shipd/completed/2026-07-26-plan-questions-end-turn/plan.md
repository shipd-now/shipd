# plan-questions-end-turn
Status: verified

## Idea

0.3.1 lists open task-shaping questions under an `OPEN QUESTIONS` header, but
still closes every digest with the go-ahead prompt ("clear enough to
proceed?"). When open questions exist that prompt is noise: the user cannot
meaningfully say "proceed" past questions only they can answer, and the two
blocks compete for the reply. The user asked for the go-ahead block to
disappear in that case.

Fix: the checkpoint turn ends in exactly one of two ways — on the `OPEN
QUESTIONS` section (when any exist; the user's typed answers are the
go-ahead), or on the typed go-ahead prompt (when none exist). Never both.

### Non-goals

- No change to the digest's findings content, the no-AskUserQuestion rule,
  the no-gate-verdict rule, or the post-gate rounds.
- No change to the go-ahead prompt's two options in the no-questions case.

Affected capabilities: `shipd-plan` (modified — `investigation-findings-digest`).
Impact: `plugins/s/skills/plan/SKILL.md`,
`plugins/s/.claude-plugin/plugin.json`.

## Implementation

- **Two mutually exclusive turn endings.** With open questions: the digest
  ends on the `OPEN QUESTIONS` list — no proceed/adjust block, no "is this
  clear" phrasing; the next user message (answers, corrections, or a bare
  go-ahead) is folded in, remaining questions carry into the post-gate
  rounds. Without open questions: the typed go-ahead prompt exactly as
  today (proceed recommended / adjust scope).
- **Version bump to 0.3.2** in `plugins/s/.claude-plugin/plugin.json`, same
  PR, per the cache-snapshot rule in AGENTS.md.

Risks: a user who wants to proceed without answering can still just say so —
the reply is free text; nothing is lost by dropping the redundant prompt.
Eval note: plan eval cases remain structurally unable to answer the
checkpoint (known since PR #31); no eval signal for this SKILL.md change.
