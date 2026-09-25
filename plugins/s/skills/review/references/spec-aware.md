# Spec-aware review

The skill reads this file when the user names a change, when exactly one change
exists under `planned/`, or when the diff adds or edits a change directory under
`planned/` or `completed/`.

Trigger when the user named a change, **or** exactly one change exists under
`planned/`, **or** the diff adds or edits a change directory under `planned/` or
`completed/`. In that last case the slug is that directory's name from the
`files` output with any leading `YYYY-MM-DD-` date prefix stripped, so
`completed/2026-09-25-my-change/` names the change `my-change`. Run
`change <name>` — it resolves `planned/<name>/` first and otherwise the newest
`completed/<date>-<name>/` archive, reporting the pick as `location`
(`planned` or `completed`) and `dir` (the change directory relative to the repo
root), so a change the build flow already archived in the pull request under
review still loads. It returns the change's status, deltas
(requirements + WHEN/THEN scenario texts), tasks (checkbox states + progress),
lint findings, and best-effort impact files. Then, against the structural diff:

- **Verify each scenario.** Classify each **Met** (cite the satisfying
  file/hunk), **Unmet** (behaviour absent), or **Can't-tell** (a first-class
  outcome — do not force it). Report every **Unmet** scenario as a
  **high-severity** spec-coverage finding; unmet requirements are the top
  finding and force a Fix-required verdict.
- **Task honesty.** Cross-check `- [x]` tasks against the diff; flag any marked
  done with no supporting change in the diff.
- **Uncovered code.** Behavioural changes no requirement or task describes are
  **observations**, not blockers.
- **Lint findings.** Surface the change's lint findings verbatim.

Report under a **Spec coverage** heading: a Met/Unmet/Can't-tell scenario
table, then the task-honesty and uncovered-code items.
