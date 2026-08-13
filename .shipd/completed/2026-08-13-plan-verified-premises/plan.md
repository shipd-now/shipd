# plan-verified-premises
Status: verified
Theme: reliability

## Idea

Require a plan that asserts how an existing command behaves to have **run** that
command before the claim reaches a spec or a task, and to cite the observation.

### Motivation

The `autopilot-in-session` build was refuted three times by the validation gate,
and every refutation was a premise the plan asserted from *reading* code rather
than running it — `--dry-run`'s member selection, `_member_column`'s inputs, and
`worktree.sh`'s idempotency. Nothing in the plan flow requires such a claim to be
exercised before it becomes a task.

### Details

- Add a premise-verification rule to the plan skill: a normative claim about an
  existing command's observable behavior must be verified by running it before
  emission, and the plan must cite what was observed.
- State it in the readiness checklist as evidence the attestation carries.
- State it in the emission guide, where `## Implementation` decisions are written.
- Add a matching requirement to the `shipd-plan` capability.

Affected capabilities: `shipd-plan` (added). Impact:
`plugins/s/skills/plan/references/readiness.md`,
`plugins/s/skills/plan/references/emission.md`,
`plugins/s/skills/plan/SKILL.md`, and the plugin version bump.

### Non-goals

- No fifth item on the readiness checklist. The four items stay as they are; this
  is evidence *within* item 3's citation discipline, not a new gate.
- No requirement to verify claims about code the change itself will write — only
  claims about behavior that already exists and can be run today.
- No change to the build or validator skills. The adversarial gate already catches
  these; this moves the catch earlier, it does not replace it.
- No new script, flag, or automated check. The rule is authoring discipline,
  enforced by the attestation and by review, not by a linter.

## Implementation

- **The rule binds only *runnable* claims about *existing* behavior.** A plan
  says many things; the ones this covers are assertions that some command,
  script, or flag that exists today behaves a particular way — the kind a task
  will then depend on. Design intent, proposed behavior, and claims about code the
  change will create are out of scope, because there is nothing to run.

- **Verification means running it, and the citation records the observation.**
  Reading the implementation is what failed three times: `select_and_order` reads
  as though it returns drivable members, `worktree.sh` reads as though a second
  invocation is harmless. The evidence is the command and what it printed or
  exited, not a file:line pointer to the source.

- **It lands as evidence under readiness item 3, not as a fifth item.** Item 3
  already demands citations for affected capabilities and files; a runnable
  premise is the same kind of obligation — say what you relied on and show it
  holds. Rejected: a fifth checklist item, which would imply every plan owes a
  verification pass even when it asserts nothing runnable.

- **Three surfaces, one rule.** `readiness.md` carries it as attestation
  evidence (where the discipline is enforced), `emission.md` carries it where
  `## Implementation` decisions are authored (where the claims get written), and
  `SKILL.md` names it in the investigation step (where the running happens). The
  wording is stated once in `readiness.md` and cross-referenced from the other
  two rather than triplicated.

- **The failure this prevents is specific and worth naming in the rule.** Two
  individually reasonable decisions can be jointly broken — `autopilot-in-session`
  chose "no run-state file, re-invoke to resume" and "call `worktree.sh` per
  member," and only running the script revealed that resuming would hard-fail.
  The rule text says so, because an abstract "verify your assumptions" is easy to
  read past.

Risk: authors may over-apply the rule and run commands to confirm claims they
never actually rely on, adding investigation cost for nothing. The rule is scoped
to claims a *task* depends on, so a premise that shapes no task needs no run.
