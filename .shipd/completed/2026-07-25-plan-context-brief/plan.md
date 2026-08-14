# plan-context-brief
Status: verified

## Idea

First real use of the depth path (shipped in `plan-depth-gate`) surfaced a UX
gap: when `am:plan` already holds rich context, the grill loop still asks one
question per turn with no surrounding narrative — the user faces a sequence of
blind dialogs with the accumulated understanding never played back. The
one-at-a-time rule was imported from grill-me for *dependent* decision chains,
but it is applied to independent decisions too, where it is only slower.
AskUserQuestion natively groups up to four questions in one call, and text
output renders before the dialog — so a better shape is fully supported by the
tooling and blocked only by our own protocol.

This change adds a context brief and grouped question rounds:

- A **context brief** precedes every decision-resolving question round on both
  paths: restate the accumulated understanding, include a diagram when it
  carries the decisions, and end with the list of open decisions — then fire
  the AskUserQuestion call.
- The depth path's grill loop partitions the agenda: **independent decisions
  are grouped** into a single AskUserQuestion call (up to the tool's cap of
  four per call); **dependent chains stay one-at-a-time**, each follow-up
  prefaced by a one-line delta of what the previous answer changed.
- The confirm-gated shared-understanding summary at the end of the depth path
  is **kept** — the brief front-loads understanding, the summary confirms the
  assembled whole before emission.

### Non-goals

- No change to the depth gate itself — signals, threshold, and overrides stay
  as shipped in `plan-depth-gate`.
- No change to the readiness checklist, emission format, or lint gate.
- No removal of the end-of-depth-path confirm summary (explicitly decided).
- No new reference files — the changes land in the existing `dialogue.md` and
  `SKILL.md`.

Affected capabilities: `shipd-plan` (modified). Impact:
`plugins/s/skills/plan/references/dialogue.md`,
`plugins/s/skills/plan/SKILL.md`,
`plugins/s/.claude-plugin/plugin.json` (version bump `0.2.4` → `0.2.5`).
Skill-markdown only — no engine tests required.

## Implementation

- **Brief applies to both paths.** Any time the skill is about to issue a
  decision-resolving AskUserQuestion round — the fast path's single batched
  call or a depth-path round — it first prints the brief: what is already
  known (so the user sees nothing will be re-asked), a diagram only when one
  carries the decisions (per `visualization.md`'s existing bar), and the open
  decisions the round will settle. Rejected: depth-only brief — the fast
  path's batched call is exactly as blind today, and the cost is a few lines.
- **The confirm gate is exempt from the brief.** The shared-understanding
  summary *is* a recap; prefacing it with another recap would be circular.
  The brief contract covers decision-resolving rounds only.
- **Partition rule in the grill loop.** When the agenda is built, split it:
  decisions whose framing does not depend on another answer are *independent*
  and go into one grouped call (up to four — the AskUserQuestion cap; a fifth+
  independent decision waits for the next round); decisions whose question
  cannot be phrased until an earlier answer lands form a *dependent chain* and
  are asked one at a time in dependency order. When unsure whether a decision
  is independent, treat it as dependent — the conservative failure mode is an
  extra round, never a question asked before its context exists. Rejected:
  always-batch — dependent choices would be posed before the answer that
  frames them.
- **Chain follow-ups get a delta-brief, not a full brief.** Inside a dependent
  chain, each follow-up question is prefaced by one line stating what the
  previous answer changed — a full recap per link would bloat the loop.
- **SKILL.md wording sync.** The fast-path question contract gains the
  brief-before-asking rule; the two places that describe the depth protocol as
  "one-decision-per-question" (the contract's scoping paragraph and the depth
  gate section) are reworded to name the grouped-round protocol, pointing at
  `dialogue.md` as the authority. The master `batched-user-questions`
  requirement's depth-path exemption wording is reconciled the same way via a
  MODIFIED entry, so no master text describes the loop as one-per-question
  after merge.
- **Version bump** `0.2.4` → `0.2.5` in
  `plugins/s/.claude-plugin/plugin.json` per the cache-snapshot rule.

Risk: mis-partitioning an agenda (calling a dependent decision independent)
would ask a question before its framing exists; guarded by the when-unsure →
dependent default, whose worst case is only an extra round. Risk: brief bloat
on trivial fast-path rounds; guarded by the existing decorative-visual
prohibition and by scoping the brief to what the round's decisions need.
