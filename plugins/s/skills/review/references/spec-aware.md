# Spec-aware review

The skill reads this file when the user names a planned change, or exactly one
change exists under `planned/`.

Trigger when the user names a change **or** exactly one change exists under
`planned/`. Run `change <name>` — it returns the change's status, deltas
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
