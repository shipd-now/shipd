# gate-poll-bridge
Status: verified

## Idea

Rework the Copilot review-gate workflow to poll for Copilot's review from
the `pull_request`-triggered run itself, because Copilot-authored review
submissions never trigger `pull_request_review` workflow runs at all.

### Motivation

Dogfooding on shipd-now-website (PRs #18/#19) proved the shipped bridge's
core trigger can never fire for exactly the reviews it exists to bridge:
Copilot submits its review from inside a dynamic Actions run with the
workflow-scoped token, and GitHub's recursion suppression means such events
create no new workflow runs — human reviews triggered gate runs within 3
seconds while Copilot's reviews produced none, so the pending status is
posted and nothing ever resolves it. The same dogfooding also disproved the
documented bootstrap limit (head-branch workflow files do trigger
`pull_request_review` runs) and surfaced a private-repo limitation (the
Copilot runner's own checkout fails, so the skill and verdict marker never
load).

### Details

- `integrations/copilot/copilot-review-gate.yml`: one gate job serving both
  triggers. The `pull_request` path posts `pending`, then polls the reviews
  API for a Copilot review of the triggering head and classifies it; the
  `pull_request_review` path (still guarded to the Copilot login and the
  current head, and still functional for any submission GitHub does route)
  classifies the event's review body directly. A per-PR concurrency group
  with cancel-in-progress stops superseded polls.
- `docs/copilot-review.md`: retract the default-branch bootstrap section,
  document the recursion-suppression reality and the polling design (with
  its runner-minutes cost and timeout semantics), and add a private-repo
  prerequisites note (checkout failure means the skill never loads and
  reviews classify fail-open).
- Version bump `0.6.131` -> `0.6.132` so existing installs report `stale`.

Affected capabilities: `copilot-review-skill` (modified), `project-readme`
(modified). Impact: `plugins/s/integrations/copilot/copilot-review-gate.yml`,
`plugins/s/skills/build/tests/test_copilot_verb.py`,
`docs/copilot-review.md`, `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No `workflow_run` trigger on the Copilot dynamic workflow — the dynamic
  run is not even listable through the Actions runs API on the dogfooding
  repo, so its addressability is unproven; rejected below.
- No scheduled reconciler, no change to `SKILL.md`, no change to the
  `shipd copilot` verb or the four-file management, no fix for the
  private-repo checkout failure (GitHub-side; documented instead).

## Implementation

- **Why polling, ADR-style.** The candidate triggers for "Copilot's review
  arrived" were: (a) `pull_request_review` — empirically never fires for
  Copilot-authored submissions (recursion suppression on workflow-token
  events, verified twice on shipd-now-website); (b) `workflow_run` on the
  Copilot dynamic workflow — unproven addressability (the dynamic run does
  not appear in the repo's Actions runs listing) and default-branch-only;
  (c) a `schedule` reconciler — 5–15 minute latency, default-branch-only,
  auto-disabled on inactive repos; (d) polling from the
  `pull_request`-triggered run — fires from the head branch (verified),
  needs no new event, and observes the review through the REST reads the
  default token already has. Chosen: (d), keeping the
  `pull_request_review` path as a free extra for human-routed submissions.
- **Workflow contract** (pinned in the delta requirement): triggers
  unchanged (`pull_request`: `opened`/`synchronize`/`reopened`;
  `pull_request_review`: `submitted`); `permissions` grants
  `statuses: write` and `pull-requests: read`; a `concurrency` group keyed
  on the pull request number with `cancel-in-progress: true`. On the
  `pull_request` path the job posts `pending` on the head SHA, then polls
  `GET /repos/{repo}/pulls/{n}/reviews` (via `gh api`, paginated) every 20
  seconds for up to 15 minutes for the newest review authored by
  `copilot-pull-request-reviewer[bot]` whose `commit_id` equals the
  triggering head SHA; each cycle it also reads the pull request's current
  head and exits quietly when the head has moved (the newer push's own run
  owns the gate). A found review is classified; a timeout leaves the
  status `pending` — no review happened, so no verdict is invented, and
  the session flow (`review_gate.py post`) remains the manual out.
- **Classification is the existing anchored last-line parse, unchanged in
  semantics.** On the polling path the body is written to a workspace file
  with `gh api --jq` output redirection and read back with a pure-bash
  `$(<file)` — never exported through the environment (sidestepping the
  128 KiB per-env-string limit) and never piped into a matcher (the
  SIGPIPE/pipefail hazard recorded in the template). The
  `pull_request_review` path keeps its `env:`-passed body. Both paths
  share one classification script block: bounded windowed trailing trim,
  last-line extraction, equality against the two markers, `fix-required`
  first, fail-open `success` with the no-verdict description otherwise.
- **Timing grounded in observation:** Copilot's reviews landed 2–3 minutes
  after request on the dogfooding repo, so 15 minutes of 20-second cycles
  is a generous bound; the run itself is the only runner cost and the
  concurrency group caps it at one live poll per pull request.
- **Docs corrections are retractions, stated as such.** The bootstrap
  section is replaced: head-branch workflow files do trigger both events'
  runs (observed), so the installing pull request needs no special
  handling; what never fires is a run for Copilot-authored review
  submissions, which the polling design absorbs. A prerequisites note
  records the private-repo observation: the Copilot runner's checkout can
  fail (`repository not found` on a private individual repo), the skill
  and marker then never load, and every review classifies fail-open — with
  the recommendation to verify the runner's checkout log once and to treat
  the session flow as the working gate where it fails.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` `0.6.131` ->
  `0.6.132`, per the cache-snapshot rule in `AGENTS.md`; it is what makes
  existing installs report `stale` for re-`add`.
