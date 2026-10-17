# ci-reviewer-approval
Status: verified
Epic: merge-rules
Planned-at: d77b207225bc087d35f8ad6aa8de52c77cab6cee
Gated-hash: d9ea017eb737

## Idea

The installed review workflow submits its verdict as `APPROVE` or `REQUEST_CHANGES` under `github.token`, and `/s:gate` offers the repository setting that lets Actions approve.

### Motivation

A repository that requires approvals cannot count the CI reviewer, because the workflow submits `COMMENT` and GitHub blocks github-actions[bot] from approving until the repository setting "Allow GitHub Actions to create and approve pull requests" is on. The setting is off on unkannybanny today, so the third identity of the epic's team test cannot approve.

### Details

- `copilot-review-gate.yml`: the CLI path's review event follows the parsed verdict (`ship-it` gives `APPROVE`, `fix-required` gives `REQUEST_CHANGES`), with the same author and rejection rules as `gate-approves`.
- New `actions_approval.py`: reads and sets the workflow approval permission through an injectable `gh` runner.
- `/s:gate` gains one optional consent row for the setting.
- Docs and plugin version bump, one patch above `main` at build time.

Affected capabilities: `copilot-review-skill` (modified), `shipd-gate` (added), `actions-approval` (new). Impact: the workflow template, `test_copilot_verb.py`, `actions_approval.py`, `plugins/s/skills/gate/SKILL.md`, two docs, `plugin.json`.

### Non-goals

- No change to `review_gate.py` (member `gate-approves`) or to identity work (`agent-identity`).
- No `shipd doctor` check of the setting (member `doctor-ruleset-drift`, which reuses `read_setting`).
- No org-level setting write and no `github.token` replacement by a PAT or App.
- No GitHub write during planning or tests.

## Implementation

- **Event rule, shared with `gate-approves`.** Success gives `APPROVE`, failure gives `REQUEST_CHANGES`, an author equal to the acting login or unreadable gives `COMMENT`, a twice-rejected decision gives a body-only `COMMENT` plus a line saying so. The workflow differs in one place: only a parsed marker is a decision (Q1), because the workflow's fail-open `success` judged nothing. The acting login is the constant `github-actions[bot]`; the author is `github.event.pull_request.user.login`, bound as `PR_AUTHOR` in the posting step's `env:`.
- **Workflow edits** (all in the classify-and-post step). Before the payload builder, `review_event` is computed in pure bash from `matched_state` and `PR_AUTHOR` (no `${var,,}`, which bash 3.2 lacks). The builder takes `REVIEW_EVENT` from its environment for `"event"`, and writes a third file, the neutral body-only `COMMENT` payload, as a sixth argument. The POST chain becomes: payload, then the plain retry under the same event, then (decision events only) a warning line and the neutral payload; a failing neutral POST still fails the step as today. The old comment saying "COMMENT, never REQUEST_CHANGES" is rewritten: a stale block clears when the next run on the new head, the same account, re-posts. Permissions need no change (`pull-requests: write` covers reviews); `github.token` stays.
- **Poll and review-event paths post no review** (Q2). Rejected: a body-only decision there, since those paths classify GitHub's own Copilot review and fail open by construction.
- **`actions_approval.py`** in `plugins/s/skills/build/scripts/`, stdlib only, run by path like `review_gate.py protect`, so it adds no `bin/shipd` verb and cannot collide with `merge-rules-config`'s `gate` dispatcher. Interface: `ENDPOINT = "repos/{nwo}/actions/permissions/workflow"`; `gh_run(args, stdin=None, cwd=None) -> (code, out, err)` (30 s timeout, same signature as `merge_rules.gh_run`); `read_setting(nwo, run) -> (state, default_perms)` with state `enabled|disabled|unknown`; `enable(nwo, run) -> (ok, message)`; `main(argv, run=gh_run, out=print) -> int` accepting `[allow] [--repo OWNER/NAME] [--root DIR]`. The repository defaults to `gh repo view --json nameWithOwner -q .nameWithOwner`. The PUT body carries the read `default_workflow_permissions` back unchanged so the write cannot loosen it.
- **Consent row** in `gate/SKILL.md` step 5 table and a new `shipd-gate` requirement (Q3): optional, run bare first to show state, never recommended by default, hint on denial in step 6.
- **Risks.** The PUT body is built from GitHub's documented schema and is unobserved by design (no write to GitHub during planning); the re-read after the write catches a silent no-op, and an organization policy can override the repository. With the setting off, every run degrades to a `COMMENT` with a warning, never a red run.

## Questions and answers

### Q1: What does the workflow submit when no verdict marker was parsed?
- **Question:** On the CLI path with no verdict marker and fail-open on, the status posts `success`. Should the review event be (1) `COMMENT`, with a decision only for a parsed marker; or (2) `APPROVE`, following the status? Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) `COMMENT`. Nothing was judged, so a bot approval would count toward required approvals without a review behind it. This narrows the status-follows rule of `gate-approves` only for the workflow.
- **Queued:** q-gate-fail-open-no-marker-review-event

### Q2: Do the poll paths submit a decision review?
- **Question:** Should the poll fallback and review-event paths also submit a decision review? Options: (1) no, only the CLI path, which authored a judged review; (2) yes, a body-only decision review following the status. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) only the CLI path. The poll paths classify GitHub's own review and post none today, and they fail open, so a bot decision there would carry no judgment. A repository that wants a CI approver sets the reviewer token.
- **Queued:** q-ci-reviewer-poll-paths-decision-review
- **Relied on by:** team-merge-test

### Q3: How does /s:gate present the Actions approval setting?
- **Question:** Options: (1) an optional consent row, recommended only when the CI reviewer should count, preserving the default workflow permissions, run only on a named consent; (2) recommended on by default; (3) documented only. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) an optional named row. It lets any workflow in the repository approve pull requests, a loosening that `protect` and auto-merge are not, so it is never preselected.
- **Queued:** q-gate-actions-approve-pr-consent-row
- **Relied on by:** team-merge-test

## Readiness attestation

### Problem and motivation

The CI reviewer cannot count as an approver: the workflow submits `COMMENT` and the repository setting that lets Actions approve is off.

Evidence:

- `plugins/s/integrations/copilot/copilot-review-gate.yml:936` sets `"event": "COMMENT"`.
- Epic `merge-rules`, Decision "The CI reviewer is the GitHub Actions bot".
- Runnable premise: `gh api repos/mikkel-bergmann/unkannybanny/actions/permissions/workflow` exited 0 and printed `{"default_workflow_permissions":"read","can_approve_pull_request_reviews":false}`.

### Scope and non-goals

The workflow's CLI-path review event, the setting reader and setter, one consent row, docs and version; the poster, identity and doctor stay out.

Evidence:

- Out of scope: `review_gate.py` (`gate-approves`), `plugins/s/bin/shipd` (`merge-rules-config`, `doctor-ruleset-drift`).
- Epic member table rows for `gate-approves`, `agent-identity`, `doctor-ruleset-drift`.

### Affected capabilities and files

Three capabilities and eight files are affected.

Evidence:

- `copilot-review-skill` requirement `gate-workflow-template` (base 23e4da77cdd6); `shipd-gate` (new requirement); `actions-approval` (new).
- Files: `plugins/s/integrations/copilot/copilot-review-gate.yml`, `plugins/s/skills/build/tests/test_copilot_verb.py`, `plugins/s/skills/build/scripts/actions_approval.py` (new) and its test, `plugins/s/skills/gate/SKILL.md`, `docs/copilot-review.md`, `docs/copilot-review-reference.md`, `plugins/s/.claude-plugin/plugin.json`.
- Event rule read from the installed `gate-approves` plan: status-keyed event, author gives `COMMENT`, double rejection gives body-only `COMMENT`.
- Runnable premise: `python3 -m unittest discover -s plugins/s/skills/build/tests` is the suite holding `test_copilot_verb.py`.

### No open task-shaping decision

Every decision is settled; three were defaulted by the planner after the oracle found no position.

Evidence:

- Marker-less review: planner default, Q1.
- Poll paths: planner default, Q2.
- Consent row: planner default, Q3.
- Reliance on `gate-approves` Q1, Q2 and Q3 for the event rule.
