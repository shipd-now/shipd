## 1. Grouped rounds and brief in dialogue.md

- [x] 1.1 [req: grill-loop] In
      `plugins/s/skills/plan/references/dialogue.md`, replace the "Resolve
      one decision per question" section with a grouped-round protocol per the
      plan's Implementation section: partition the agenda into independent
      decisions (grouped into one AskUserQuestion call of up to four, each
      with the recommended option listed first) and dependent chains (asked
      one at a time in dependency order); state the when-unsure → dependent
      default; keep the fold-back step, the end-at-readiness condition, and
      the ~6-item soft cap unchanged.
- [x] 1.2 [req: context-brief] In the same `dialogue.md`, add a "Context
      brief" section: every decision-resolving round opens with a
      restatement of the accumulated understanding, a diagram only when one
      carries the decisions (defer to `visualization.md`'s bar), and the list
      of open decisions, with the AskUserQuestion call issued in the same
      turn; state the two exemptions — the shared-understanding summary needs
      no preceding brief, and dependent-chain follow-ups take a one-line
      delta statement instead of a full brief.

## 2. SKILL.md wording sync

- [x] 2.1 [req: context-brief] In `plugins/s/skills/plan/SKILL.md`, add the
      brief-before-asking rule to "The fast-path question contract": before
      the single batched call, present what is already known and the open
      decisions the call will settle, in the same turn as the call.
- [x] 2.2 [req: grill-loop] In the same `SKILL.md`, reword the two
      descriptions of the depth protocol as "one-decision-per-question" (the
      contract's scoping paragraph and the depth gate section) to describe the
      grouped-round protocol — independent decisions grouped, dependent
      chains one at a time — naming `dialogue.md` as the authority.

## 3. Version bump and review

- [x] 3.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.2.4` to `0.2.5`.
- [x] 3.2 [req: *] Re-read the edited `SKILL.md` and `dialogue.md` together
      with `references/readiness.md`, `references/emission.md`, and
      `references/visualization.md`; confirm no rule contradicts another
      (brief on both paths, confirm summary kept and exempt from the brief,
      grouping only in the depth loop, readiness gate unchanged); fix any
      contradiction found.
