# copilot-review-gate
Status: verified

## Idea

Bridge GitHub Copilot's code review into the required `semantic-review`
commit status with a fourth `shipd copilot`-managed file — a real
PR-triggered gate workflow — so a repository's merges no longer hang on a
status nothing posts.

### Motivation

The Copilot integration is advisory by design: it never sets the required
`semantic-review` status, so on a repo whose branch protection requires that
context (verified live on shipd-now-website#17), every pull request waits
forever at "Expected — waiting for status to be reported" unless a Claude
session runs the review-gate flow by hand.

### Details

- New template `integrations/copilot/copilot-review-gate.yml`: a workflow
  that posts `semantic-review` = `pending` on pull-request open/update and
  bridges Copilot's submitted review into `success`/`failure` on the head
  commit.
- `integrations/copilot/SKILL.md` gains a machine-readable verdict marker
  the review must end with, and its advisory scope section is rewritten to
  describe the gate.
- `shipd copilot` (in `plugins/s/bin/shipd`) manages four files instead of
  three; report/add/remove stay table-driven.
- `docs/copilot-review.md` gains a merge-gate section.

Affected capabilities: `shipd-cli` (modified), `copilot-review-skill`
(modified + added requirement), `project-readme` (modified). Impact:
`plugins/s/bin/shipd`, `plugins/s/integrations/copilot/`,
`plugins/s/skills/build/tests/test_copilot_verb.py`,
`docs/copilot-review.md`, `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No step that requests Copilot as a reviewer — triggering stays
  GitHub-side (branch ruleset or manual request), per Q2.
- No change to `review_gate.py`: the session flow keeps posting the same
  context; either poster satisfies the required check.
- No model pinning, no secrets beyond the workflow's own `github.token`,
  no change to the existing setup workflow
  (`copilot-code-review.yml`).

## Implementation

- **The gate is a fourth managed file, not an extension of the setup
  workflow.** `copilot-review-skill/setup-workflow-template` mandates the
  existing `copilot-code-review.yml` carry exactly one job named
  `copilot-setup-steps`, so the gate lands as its own template,
  `integrations/copilot/copilot-review-gate.yml`, installed to
  `.github/workflows/copilot-review-gate.yml`. Rejected: adding jobs to the
  setup workflow — it would break that requirement and conflate the Copilot
  runner environment with the Actions gate.
- **Workflow contract** (pinned in the delta spec's
  `gate-workflow-template` requirement): triggers `pull_request`
  (`opened`/`synchronize`/`reopened`) and `pull_request_review`
  (`submitted`); a `permissions` block granting `statuses: write`; status
  posts via `gh api repos/.../statuses/<head-sha>` authenticated by
  `github.token` (`gh` ships on `ubuntu-latest`). On `pull_request` events
  the status is `pending`; on `pull_request_review` events the workflow
  acts only when the review author login is
  `copilot-pull-request-reviewer[bot]` (observed verbatim on
  shipd-now-website#17) and the review's `commit_id` equals the PR's
  current head SHA, so stale reviews of older commits are ignored.
- **Verdict mapping is fail-open (Q1, user-settled).** Body containing
  `<!-- shipd-verdict: fix-required -->` posts `failure`; containing
  `<!-- shipd-verdict: ship-it -->` posts `success`; containing neither
  posts `success` with a description stating no verdict was parsed.
  Rationale: skill pickup is heuristic — a live review on
  shipd-now-website#17 ignored the installed skill entirely, so fail-closed
  would block merges whenever Copilot skips it. Rejected: fail-closed.
- **The SKILL.md template mandates the marker.** The review must end with
  a visible verdict line and the matching HTML comment marker
  (`<!-- shipd-verdict: ship-it -->` or
  `<!-- shipd-verdict: fix-required -->`), keeping the workflow's parse an
  exact substring match rather than prose inference. The template's scope
  section is rewritten: the review drives the `semantic-review` status when
  the gate workflow is installed, fail-open on a missing marker.
- **Status context stays `semantic-review`** — the same context
  `review_gate.py` posts (its `CONTEXT` constant), so the branch-protection
  required check (`app_id: null`, any poster accepted — observed on the
  live branch-protection API) is satisfied by whichever poster ran last.
- **Verb wiring is table-driven.** `plugins/s/bin/shipd` adds the fourth
  path to `COPILOT_MANAGED` and a `COPILOT_TEMPLATED` entry reusing the
  `# shipd-copilot v{version}` marker pattern; `copilot_states`,
  `_copilot_add`, and `_copilot_remove` already iterate those tables.
  `remove` deletes files only, so `.github/workflows/` is never pruned.
- **Known limit, documented not solved:** on pull requests from forks the
  `pull_request_review` token is read-only, so the gate cannot post the
  status there; same-repo branches (the shipd flow) are unaffected.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` `0.6.126` →
  `0.6.127`, per the cache-snapshot rule in `AGENTS.md`.

## Questions and answers

### Q1: What does the gate post when Copilot's review has no verdict marker?
- **Question:** When Copilot submits a review on the current head whose body
  carries no parseable shipd verdict marker (skill pickup is heuristic —
  verified live that Copilot can ignore the skill), should `semantic-review`
  be (a) fail-open `success` with a no-verdict description, a parsed
  `fix-required` still posting `failure`, or (b) fail-closed `failure` until
  a parseable verdict appears? Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Fail-open — option (a). The gate means "Copilot has reviewed
  this head commit"; the description states when no verdict was parsed, and
  a skill-driven `fix-required` still blocks. Fail-closed would brick merges
  whenever Copilot skips the skill.
- **Queued:** none — no discoverable workspace, nothing was filed.

### Q2: Should the gate workflow request Copilot as a reviewer itself?
- **Question:** Should the workflow best-effort request
  `copilot-pull-request-reviewer[bot]` on pull-request open
  (continue-on-error), or leave triggering entirely GitHub-side and only
  bridge review to status? Recommendation: GitHub-side only.
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** No request step. The verified enablement model names exactly
  two triggering paths, both GitHub-side — a per-PR reviewer request and a
  branch ruleset — and the research report's plan-gating finding shows a
  token-driven request cannot be relied on (Copilot seats are plan-gated).
  A request step would contradict the documented model, not just add noise.
- **Cited:** verified/project-readme, research/copilot-code-review
