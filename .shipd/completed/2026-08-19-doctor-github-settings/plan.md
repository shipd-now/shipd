# doctor-github-settings

Status: verified

## Idea

Teach `shipd doctor` to detect missing GitHub-side merge-gate settings —
branch protection requiring `semantic-review`, auto-merge allowance, and the
gate's `COPILOT_GITHUB_TOKEN` secret — and teach `/s:doctor` to fix them
through consent-gated `gh api` calls.

### Motivation

A live test (shipd-now-website PR #22 follow-up) showed the copilot gate
degrades silently on a repo whose GitHub settings are missing: nothing
requires the `semantic-review` status, so PRs merge with the verdict ignored,
and no shipd surface detects it — doctor's ten checks are all local, and
`shipd copilot add` is contractually file-only.

### Details

- Three new read-only doctor checks, reported after `statusline`:
  `protection` (default branch protected and requiring `semantic-review`),
  `automerge` (repo allows auto-merge, waived under `pr-mode: draft`), and
  `copilot-secret` (gate workflow installed but no `COPILOT_GITHUB_TOKEN` →
  names the fail-open poll fallback).
- Three new `/s:doctor` remedy rows running the matching `gh api` fixes on
  consent; the un-automatable secret (a human must mint the PAT) becomes a
  hand-off like `gh auth login`.

Affected capabilities: `shipd-cli` (added requirement), `shipd-doctor`
(modified requirement). Impact: `plugins/s/bin/shipd`,
`plugins/s/skills/doctor/SKILL.md`,
`plugins/s/skills/build/tests/test_shipd_cli.py`, `docs/copilot-review.md`,
plugin version bump.

### Non-goals

- No change to `shipd copilot add` — its "no network, no `gh`" contract
  stands; detection lives in doctor only.
- No automatic creation of the `COPILOT_GITHUB_TOKEN` PAT or any interactive
  command — those stay user hand-offs.
- No ruleset management (e.g. the "require Copilot review" ruleset) — the
  docs already route that to the Settings UI.
- No reconciliation of `project-readme`'s stale quickstart check enumeration
  (it already omits `pipeline`/`difft`/`statusline`).

## Implementation

- **Detection in the CLI verb, fixes in the skill.** Mirrors the existing
  split exactly: the verb stays read-only ("The verb SHALL mutate nothing"),
  `/s:doctor` owns consent-gated mutation. Rejected: checks in
  `shipd copilot add` — it would break that verb's documented no-network
  contract.
- **A separate ADDED `shipd-cli` requirement (`doctor-github-checks`), not a
  `doctor-verb` edit.** Precedent: pr-mode validation shipped as its own
  `doctor-pr-mode-check` requirement without reopening the large `doctor-verb`
  block.
- **One repo probe, shared.** `gh api repos/<nwo>` returns `default_branch`,
  `allow_auto_merge`, and `permissions.admin` in one call (observed live this
  session against `shipd-now/shipd`); `<nwo>` resolves from the working
  directory via `gh repo view --json nameWithOwner -q .nameWithOwner`. The
  payload is fetched once and reused by `protection` and `automerge`; its
  `permissions.admin` is surfaced in warn details so the skill knows whether
  fixes are even possible.
- **Tiered protection probe.** `branches/<default>/protection` returns
  `required_status_checks.contexts` for admins (observed: `["ci",
  "semantic-review"]` on shipd) and 404s when unprotected; on 403 (non-admin)
  fall back to the branches listing's `protected` boolean (observed
  readable without admin). Contexts-unverifiable outcomes report `ok` with a
  note, never a false warn.
- **Every degradation is `warn` or `ok`, never `fail`.** Doctor convention:
  `fail` is reserved for cannot-work-at-all; `gh` itself only ever warns. No
  GitHub remote, unauthenticated `gh`, offline, or any `gh api` error →
  `ok <check> — skipped: <why>`. The preflight must never break offline.
- **`automerge` is pr-mode-aware.** `sc.resolve_pr_mode(root)` (values
  `auto`|`draft`) already loads in `check_config`; under `draft` the flow
  never arms auto-merge, so `allow_auto_merge: false` reports `ok` with a
  draft-mode note.
- **`copilot-secret` activates on the gate file.** Only when
  `.github/workflows/copilot-review-gate.yml` exists at the working-directory
  root; the secret only matters to that workflow. Repo-level
  `actions/secrets` listing observed working (found `COPILOT_GITHUB_TOKEN` on
  the website repo, `{"total_count":0}` on shipd); the org-secrets endpoint
  422s on user-owned repos, so it is not probed.
- **Fix commands (consent-gated, in the skill).** Unprotected branch →
  `gh api -X PUT repos/<nwo>/branches/<default>/protection` with the minimal
  body (`required_status_checks: {strict: false, contexts:
  ["semantic-review"]}`, `enforce_admins: false`,
  `required_pull_request_reviews: null`, `restrictions: null`). Protected but
  missing the context → `gh api -X POST
  .../protection/required_status_checks/contexts -f "contexts[]=
  semantic-review"`, which appends without clobbering existing contexts such
  as shipd's own `ci`. Auto-merge off → `gh api -X PATCH repos/<nwo> -F
  allow_auto_merge=true`. All three require admin; when the finding's detail
  says admin is missing, the skill treats it as report-only.
- **Injection points for tests.** Each check takes an injectable runner
  (defaulting to the real `gh` subprocess), matching `check_gh`'s pattern, so
  `tests/test_shipd_cli.py` stays offline; `_gh_auth_status`'s "the one
  subprocess in the doctor path" comment is updated to name the new probes.
- **Version bump.** `plugins/s/` changes, so
  `plugins/s/.claude-plugin/plugin.json` bumps to the next patch version current at ship time (0.6.140 as of this build) in the same
  PR.

Risk: GitHub API shapes drift (e.g. `permissions` absent on some token
types); guarded by treating every missing field or non-200 as
skipped/unverifiable `ok`, so drift degrades to silence, not false alarms.
Risk: a PUT-protection remedy on a repo with existing protection would
clobber it; guarded by only offering PUT on the 404 (unprotected) finding and
the append endpoint on the missing-context finding.
