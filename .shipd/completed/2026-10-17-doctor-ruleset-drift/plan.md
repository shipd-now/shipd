# doctor-ruleset-drift
Status: verified
Epic: merge-rules
Planned-at: d77b207225bc087d35f8ad6aa8de52c77cab6cee
Gated-hash: b262419bfa42

## Idea

Make `shipd doctor` read repository rulesets as protection, report drift between the `merge` config and the live `shipd merge rules` ruleset, and report whether Actions may approve.

### Motivation

Repository owners whose default branch is protected by a ruleset are told it is "not protected", and nothing tells them the applied rules drifted from config. Observed: the `protection` check on unkannybanny `main` (ruleset 25150897, classic protection 404) warns the branch is unprotected.

### Details

- `check_protection` also reads `gh api repos/<nwo>/rules/branches/<default>` and judges the union of required contexts.
- New check `merge-rules`: config versus live ruleset, via `merge_rules.find_owned`, `live_members`, `diff` and `resolve_merge`.
- New check `actions-approve`: the Actions `can_approve_pull_request_reviews` setting.
- Doctor skill rows, and a plugin version bump.

Affected capabilities: `shipd-cli` (modified, added), `shipd-doctor` (added).

Dependency: builds after `merge-rules-config` merges; it consumes `plugins/s/skills/build/scripts/merge_rules.py` and `resolve_merge` in `plugins/s/skills/build/scripts/spec_common.py`, neither on main yet.

### Non-goals

- No fixing: doctor reads only; fixes stay in `/s:gate` (`shipd gate rules apply`).
- No change to `merge_rules.py` or the `merge` key; no org-ruleset editing.

## Implementation

- **Protection.** In `check_protection` keep the classic probe; when it does not already show `semantic-review`, call `_branch_rules` (`rules/branches/<branch>`, readable without admin). Union the classic contexts with contexts of `required_status_checks` rules. Ok names the source; protected-without-context warns, naming the ruleset when that is the source; "not protected" only if classic is 404 and the list is `[]`. A failing rules probe keeps the classic outcome. Rejected: replacing the classic probe, since repos still use it.
- **merge-rules.** `check_merge_rules(root, context, run=_gh_run, merge_rules=None)`: skip context gives ok; `sc.resolve_merge(root)` ConfigError gives warn naming it; adapt the runner as `lambda args, stdin=None, cwd=None: run(args)` and call `merge_rules.find_owned(nwo, adapted)` assumed to return the owned ruleset detail or None. None gives warn (live approvals absent, run `shipd gate rules apply`); otherwise `diff(merge, detail)`; empty gives ok, else warn `member: live X, wanted Y` joined by `; ` plus a pointer to `shipd gate rules`. Any exception from the lookup (including a duplicate-named ruleset, whose message names it) gives ok "could not be verified: <message>". Build step: read the merged `merge_rules.py` first and fit these calls to its real signatures.
- **actions-approve.** `check_actions_approve`: only where `copilot-review-gate.yml` exists; probe `actions/permissions/workflow`. Observed on unkannybanny: `{"default_workflow_permissions":"read","can_approve_pull_request_reviews":false}`.
- **Placement.** Both checks follow `fast-pass` in `check_steps`, sharing the lazily resolved context; existing name-list tests change.
- **Observed premise.** The current doctor logic (`check_protection` with the unkannybanny context) returned `warn protection ... not protected`; `gh api repos/mikkel-bergmann/unkannybanny/rules/branches/main` exited 0 listing `required_status_checks` with `ci` and `semantic-review`.
- Risks: `find_owned` return shape differs from the assumption (guard: build reads it first); new stub keys break old tests (task 1.2).

## Questions and answers

### Q1: Level when the shipd ruleset is absent?
- **Question:** What does `merge-rules` report when no `shipd merge rules` ruleset exists? Options: (1) warn naming `shipd gate rules apply`; (2) ok with a note; (3) warn only when config declares `merge`. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Warn, option 1. An unapplied rule is the drift this epic exists to surface, and warnings never fail the preflight.
- **Queued:** q-doctor-merge-rules-missing-ruleset-level

### Q2: How is drift shown given one line per check?
- **Question:** Options: (1) one `warn merge-rules` line listing differing members joined by `; `, pointing at `shipd gate rules`; (2) let a check return several lines; (3) one check per member. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** One line, option 1. The skill parses one line per check, and `shipd gate rules` already prints the member-per-line report.
- **Queued:** q-doctor-ruleset-drift-line-format

### Q3: When does `actions-approve` warn?
- **Question:** Options: (1) new check after `merge-rules`, probed only where the gate workflow is installed, warn when false; (2) probe always, warn when false; (3) always ok, state only. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The setting matters only to the installed review workflow, so repos without it get no noise.
- **Queued:** q-doctor-actions-approve-warn-condition

### Q4: How does protection read rulesets?
- **Question:** Options: (1) keep the classic probe and add the effective branch rules, union of contexts, same check name; (2) rulesets only; (3) list rulesets and fetch each detail. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The branch-rules endpoint includes organisation rulesets, needs no admin, and costs one call.
- **Queued:** q-doctor-protection-reads-rulesets

## Readiness attestation

### Problem and motivation

Ruleset-protected repositories are called unprotected and rule drift goes unreported.

Evidence:

- `plugins/s/bin/shipd` `check_protection` reads only `branches/<default>/protection`.
- Epic `merge-rules` Decision "Doctor verifies, never silently fixes".

### Scope and non-goals

Read-only checks and skill rows; no fixes and no engine module changes.

Evidence:

- Out of scope: `merge_rules.py` (owned by `merge-rules-config`).
- Capability `shipd-doctor` remedy boundaries keep GitHub writes consent-gated.

### Affected capabilities and files

Two capabilities and four files, because checks, tests, skill and version each take one edit.

Evidence:

- Capabilities: `shipd-cli` (`doctor-github-checks` base 87a74d8dd224, new check requirements), `shipd-doctor` (new requirement).
- Files: `plugins/s/bin/shipd` (`check_protection`, `check_steps`, `REMEDY_SURFACES`), `plugins/s/skills/build/tests/test_shipd_cli.py`, `plugins/s/skills/doctor/SKILL.md`, `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `check_protection` on the unkannybanny context returned `warn protection` saying not protected.
- Runnable premise: `gh api repos/mikkel-bergmann/unkannybanny/rules/branches/main` exited 0 and listed the required checks.
- Runnable premise: `gh api repos/mikkel-bergmann/unkannybanny/actions/permissions/workflow` exited 0 with `can_approve_pull_request_reviews` false.

### No open task-shaping decision

Every decision is settled; none remain.

Evidence:

- Absent-ruleset level: Q1, planner default.
- Drift line format: Q2, planner default.
- Actions check scope: Q3, planner default.
- Ruleset read method: Q4, planner default.
- Reuse of `merge-rules-config` Q1 (no merge-method pinning, so `diff` ignores it): planner default there.
