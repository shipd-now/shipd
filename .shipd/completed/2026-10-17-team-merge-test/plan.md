# team-merge-test
Status: verified
Epic: merge-rules
Theme: reliability
Planned-at: d77b207225bc087d35f8ad6aa8de52c77cab6cee
Gated-hash: cd686a6dc8c7

## Idea

Prove on the unkannybanny test repo that GitHub itself enforces the merge rules for a team of three identities, with a repeatable driver and a committed evidence record.

### Motivation

The epic's success criterion is that a rerun of the unkannybanny test merges only after GitHub records two approvals from non-author identities, and no one has run that. The owner cannot trust the merge-rules members until a real pull request shows each rule blocking and then releasing.

### Details

- Add `tools/team_merge_test.py`, a stdlib driver with verbs `preflight`, `apply`, `run`, and `report`, plus `tools/tests/test_team_merge_test.py` on a fake `gh` runner (no GitHub in tests).
- Add the how-to `docs/team-merge-test.md` and, from the live run, the evidence record `docs/retros/<run-date>-team-merge-test.md` rendered by `report`.
- Live steps at build time, on unkannybanny only: a prep pull request, the ruleset apply, one throwaway pull request that proves (a) to (e).

Affected capabilities: `team-merge-test` (added). Impact: `tools/`, `docs/`; nothing under `plugins/s/`, so no version bump.

### Non-goals

- No change to `plugins/s/`; the other members own every shipped behavior.
- No write to GitHub during planning, and none ever to shipd-now/shipd.
- No creation of the second account or its token, and no token in chat, files, or evidence.

## Implementation

- **Driver safety.** `ALLOWED_REPO = "mikkel-bergmann/unkannybanny"`; any other `--repo` exits 2 before a call. `Gh.run(args, who="author"|"reviewer", stdin=None, cwd=None) -> (code, out, err)`. Reviewer env is a copy of `os.environ` with `GH_TOKEN` from `TEAM_TEST_REVIEWER_GH_TOKEN` or `GH_CONFIG_DIR` from `TEAM_TEST_REVIEWER_GH_CONFIG_DIR`; the reviewer login is read from `gh api user` and never hardcoded. Output and evidence are redacted of the token value.
- **Preflight** prints `ok|missing <name> - <fix>` and exits 3 on any miss; `--only user` checks the user prerequisites, `--only repo` the prep state. User: reviewer env set and `gh api user` works under it; reviewer login differs from the author's; `collaborators/<login>/permission` is write or admin; `actions/permissions/workflow` shows `can_approve_pull_request_reviews` true. Repo: `COPILOT_GITHUB_TOKEN` secret exists (observed), the main-branch gate workflow carries `PR_AUTHOR`, and `.shipd-config.json` carries the `merge` block.
- **Apply.** Runs `shipd gate rules apply --repo ... --root <clone>`, then reads the live ruleset itself and asserts approvals 2, dismiss_stale, last_push_approval, thread resolution, checks `ci` and `semantic-review`, no bypass actors, independent of shipd's own diff.
- **Run** uses a fresh branch `team-merge-test/<UTC stamp>` and one pull request, auto-merge unarmed until step 5. Every assertion records a GitHub server fact (`id`, `claim`, `observed`, `ok`, `at`) to `evidence.json`; it stops on the first failure and leaves the PR open.
  1. Wait for green `ci`, `semantic-review`, and the github-actions[bot] APPROVED review on the head. (a): `PUT pulls/N/merge` returns 405, `mergeStateStatus` BLOCKED, one approval.
  2. (c): the author's `gh pr review --approve` fails with GitHub's own-PR refusal, and `shipd room whoami N` as author exits 1.
  3. The reviewer runs `whoami` (exit 0), approves the head sha; two approvals, state CLEAN, no merge.
  4. (b): the author pushes a content edit (GitHub keeps approvals across an empty commit, whose diff is unchanged); the reviewer review reads DISMISSED, the merge probe returns 405 while checks go green, and only the bot re-approves.
  5. (d): record head sha and zero unresolved threads (GraphQL), arm `gh pr merge --auto --squash` (still OPEN with one approval), the reviewer approves that sha, poll to MERGED; assert two APPROVED reviews on the head from logins other than the author.
  6. (e): `shipd doctor` in the clone shows no `warn` or `fail` for `protection`, `merge-rules`, `actions-approve`; the bare `shipd gate rules` shows no `differs`.
- **Prep PR** (live): in the unkannybanny clone `/Users/mikkelbergmann/projects/workspaces/unkannybanny/unkannybanny`, `shipd copilot add` and an explicit `merge` block, merged under the existing 0-approval `main` ruleset before apply. Risk: pushing a workflow file needs `workflow` token scope; the build reports it and stops.
- **Pure helpers** for tests: `classify_probe`, `approvals_on_head`, `redact`, `render_report`, `check_prereqs`.

## Questions and answers

### Q1: Where does the proof live?
- **Question:** Options: (1) stdlib driver under `tools/` with fake-runner tests, a how-to, and a retro evidence record, live writes only at build time; (2) a how-to only; (3) live steps only. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1). A scripted driver makes the proof repeatable and reviewable; repo-only tooling lives under `tools/`.
- **Queued:** q-team-merge-test-proof-home

### Q2: How does the driver get the reviewer identity?
- **Question:** Options: (1) user-exported `TEAM_TEST_REVIEWER_GH_TOKEN` or `TEAM_TEST_REVIEWER_GH_CONFIG_DIR` mapped into the reviewer subprocess only; (2) a whole reviewer session with `GH_TOKEN`; (3) a token file argument. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1). It follows agent-identity's environment-only rule, keeps the token out of files and arguments, and one process can act as both accounts.
- **Queued:** q-team-test-reviewer-identity-input

### Q3: How is unkannybanny prepared?
- **Question:** Options: (1) a prep PR installing the gate files and an explicit `merge` block, merged before apply; (2) apply from a scratch config; (3) no gate workflow. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1). The bot approver exists only with the gate workflow, and a committed `merge` block makes the repo the source of truth for both apply and doctor.
- **Queued:** q-test-repo-prep-for-gate-rules

### Q4: What counts as proof?
- **Question:** Options: (1) recorded GitHub server facts, merge probe 405, review states, raw refusals, final merged state, auto-merge armed last; (2) watch until merged; (3) agent-reported status. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1). Only server facts show GitHub, not the agents, enforced each rule; arming last stops a bug from merging early.
- **Queued:** q-e2e-merge-rules-github-server-evidence

## Readiness attestation

### Problem and motivation

No end-to-end run shows GitHub enforcing the merge rules with three identities, and the epic's first success criterion needs one.

Evidence:

- Epic `merge-rules` success criteria and the `team-merge-test` row of its Changes table.
- Capability `semantic-review`: the gate today posts only `COMMENT` reviews.

### Scope and non-goals

The change adds a driver, a how-to, and an evidence record; shipped plugin behavior stays with the five earlier members.

Evidence:

- In scope: `tools/team_merge_test.py`, `tools/tests/test_team_merge_test.py`, `docs/team-merge-test.md`, `docs/retros/`.
- Out of scope: `plugins/s/` (the epic Decision that each member owns its seam).

### Affected capabilities and files

One new capability and four new files; nothing existing is edited except the how-to docs index if any.

Evidence:

- Capability `team-merge-test` (new). Files above; CI already runs `python3 -m unittest discover -s tools/tests` (`.github/workflows/ci.yml:36`).
- Runnable premise: `gh api repos/mikkel-bergmann/unkannybanny/collaborators --jq '.[].login'` printed only `mikkel-bergmann`, so the second account is missing today.
- Runnable premise: `gh api repos/mikkel-bergmann/unkannybanny/actions/permissions/workflow` printed `can_approve_pull_request_reviews` false.
- Runnable premise: `gh api repos/mikkel-bergmann/unkannybanny/rulesets/25150897` showed approvals 0, no dismiss_stale, checks `ci` and `semantic-review`.
- Runnable premise: `gh api repos/mikkel-bergmann/unkannybanny/contents/.github/workflows` listed `ci.yml` and `room-wake.yml` only, and the secrets list held `COPILOT_GITHUB_TOKEN`.

### No open task-shaping decision

Every decision is settled; Q1 to Q4 took the planner default after the oracle returned insufficient.

Evidence:

- Q1 proof home, Q2 reviewer identity input, Q3 repo prep, Q4 proof standard: PLANNER defaults.
- Interfaces consumed from earlier members: `shipd gate rules apply`, `shipd room whoami`, the bot approval, `merge-rules` doctor line.
