# copilot-cli-gate
Status: verified

## Idea

Give the review gate a first-class reviewer: when a `COPILOT_GITHUB_TOKEN`
secret is configured, the gate workflow runs the shipd semantic review
itself through headless GitHub Copilot CLI — which can execute the bundled
engine and emit the verdict marker — instead of waiting on GitHub's Copilot
code-review surface, which cannot.

### Motivation

The public-repo test proved GitHub's Copilot code-review agent runs with
its bash tool disabled and assembles the review body in its own pipeline,
so the shipd engine can never execute and the verdict marker can never
appear — the strict gate was unreachable on every repo, and on private
repos the runner cannot even check the repo out. A live probe showed
headless Copilot CLI does everything the contract needs: it ran both
`semdiff.py` subcommands, reasoned from the structural hunks, and ended
its output with the exact marker line.

### Details

- `integrations/copilot/copilot-review-gate.yml`: on `pull_request`, after
  posting `pending`, branch on the `COPILOT_GITHUB_TOKEN` secret — present:
  check out the head with full history, install difftastic and ripgrep,
  install `@github/copilot`, run `copilot -p` instructed to follow the
  installed SKILL.md and end with the marker, classify the output's last
  non-empty line, post the strict status and the review text as a PR
  comment; absent: the existing poll path, unchanged.
- `integrations/copilot/SKILL.md`: correct the stale "exact substring
  match" sentence to the last-non-empty-line equality reality, and state
  the skill is the contract for both reviewer surfaces.
- `docs/copilot-review.md`: document the CLI reviewer mode — the secret
  (a fine-grained PAT with the account-level "Copilot Requests"
  permission), behavior, per-review AI-credit cost, that it works on
  private repositories, and today's CCR-surface reality.
- Version bump `0.6.132` -> `0.6.133`.

Affected capabilities: `copilot-review-skill` (modified),
`project-readme` (modified). Impact:
`plugins/s/integrations/copilot/copilot-review-gate.yml`,
`plugins/s/integrations/copilot/SKILL.md`,
`plugins/s/skills/build/tests/test_copilot_verb.py`,
`docs/copilot-review.md`, `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No change to the poll path's semantics — it stays the exact fallback
  when the secret is absent, and the `pull_request_review` bridge keeps
  its guards.
- No step requesting Copilot as a CCR reviewer (standing decision), and no
  removal of the CCR-oriented pieces — a repo may still use both surfaces.
- The three non-SKILL findings from the selftest review (setup-workflow
  find guard, tarfile regular-file check, `blob_at` empty-vs-missing
  ambiguity) stay a separate follow-up change.

## Implementation

- **Why Copilot CLI, ADR-style.** The CCR surface is structurally unable
  to satisfy the contract (bash tool disabled, pipeline-assembled body —
  observed in the run log), and no user-side setting changes that. Copilot
  CLI in the gate's own Actions job restores full control: it executes the
  engine, authors the body, and runs under the normal Actions checkout —
  which also works on private repositories, closing that limitation.
  Rejected: an Anthropic-API reviewer (new billing surface; the user's
  Copilot subscription already covers CLI credits); waiting for GitHub to
  enable CCR's bash tool (not actionable).
- **Workflow contract** (pinned in the delta requirement). Triggers,
  permissions base, and concurrency are unchanged; `permissions` adds
  `pull-requests: write` for the review comment. The `pull_request` path
  posts `pending`, then branches on the secret exposed as an env var:
  - **CLI path** (secret non-empty): check out the head SHA with
    `fetch-depth: 0` (the engine's merge-base diff needs history), fetch
    the base ref, install difftastic (release tarball, the setup
    workflow's pattern) and ripgrep, `npm install -g @github/copilot`,
    then run `copilot -p` — the prompt names the installed
    `.github/skills/code-review/SKILL.md` as the instructions to follow,
    names the base and head refs to diff, forbids the CLI from posting
    anything itself, and requires the marker as the last line —
    with `--allow-all-tools`, `COPILOT_GITHUB_TOKEN` from the secret, and
    a bounded runtime (`timeout` ~600s), capturing stdout to a workspace
    file. Classify the captured output's last non-empty line with the
    existing pure-bash extraction: `fix-required` -> `failure`, `ship-it`
    -> `success`, any other line -> fail-open `success` with the
    no-verdict description (the user's standing fail-open answer applies
    to this path too). A nonzero/timed-out CLI run posts nothing further —
    `pending` stands, exactly like a poll timeout, with the session flow
    as the manual out. The review text is posted as a PR comment via
    `gh` so humans read what the gate judged, whatever the verdict.
  - **Poll path** (secret empty): byte-for-byte today's behavior.
  The `pull_request_review` bridge path is untouched.
- **Secrets carve-out.** The template's no-secrets rule becomes: no secret
  other than the workflow's own `github.token` and the single optional
  `${{ secrets.COPILOT_GITHUB_TOKEN }}`, which only feeds the CLI's env —
  never `gh`, whose calls stay on `github.token`.
- **SKILL.md is the single review contract.** The CLI prompt defers to the
  installed SKILL.md rather than duplicating the review instructions in
  YAML, so the rubric lives in one file for both surfaces. Its stale
  "exact substring match" sentence (flagged by the selftest review)
  becomes: the marker is read from the body's last non-empty line by
  exact equality.
- **Runnable premises, verified live:** headless auth via the
  `COPILOT_GITHUB_TOKEN`/`GH_TOKEN` env (the CLI's own error names them;
  a `pong` run succeeded once the PAT gained the "Copilot Requests"
  account permission); engine execution and marker obedience (the CLI ran
  both `semdiff.py` subcommands against a real commit and ended with the
  exact marker line — 6.64 AI credits, 16 seconds); global npm install of
  `@github/copilot` (29 seconds locally). Runner-side `npm`/`timeout` are
  standard on `ubuntu-latest`.
- **Cost and bounds:** one CLI review per push (the existing per-PR
  concurrency cancels superseded runs); observed ~7 credits for a small
  review, documented so a repo can budget against its monthly credits.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` `0.6.132` ->
  `0.6.133`, per the cache-snapshot rule in `AGENTS.md`; existing installs
  report `stale` and refresh on re-`add`.
