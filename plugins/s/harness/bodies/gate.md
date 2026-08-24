<!-- description: Set up the shipd semantic review gate in a repository, taking consent before anything changes on GitHub. -->
# /s:gate — install the review gate, with consent

Run the existing engines in order: install the files, commit them, require the
check, hand off the reviewer token, verify. Invent no mechanism, and change
nothing the user did not approve. One setup round per invocation. The `update`
argument runs the closing refresh-only section in place of steps 2–7.

<!-- include:preamble -->

## 1. Preflight

Confirm all three before writing anything, **in this order**: a git repository
(`git rev-parse --show-toplevel`), `gh` authenticated (`gh auth status`), and a
GitHub repository resolving (`gh repo view --json nameWithOwner` — keep the
`<nwo>`; it cannot succeed unauthenticated, so checked first it would mask a
missing login). If any fails, report what is missing, run no install and no
mutation, and stop: a missing `gh` gets its install command; an
unauthenticated one gets `gh auth login`, handed over — never run it, it is
interactive.

## 2. Install the four files

Run `shipd copilot add` and relay its per-file report verbatim. It is offline,
idempotent, and touches exactly `.github/skills/code-review/SKILL.md`, that
directory's `scripts/semdiff.py`, `.github/workflows/copilot-code-review.yml`,
and `.github/workflows/copilot-review-gate.yml`. If it refuses because a
managed path is foreign, report the file it named and stop — never pass
`--force` on your own judgement.

## 3. Commit and push them

Copilot reads skills and workflows from the PR's **head branch** — files left
on disk are invisible to the review. Propose the commit and push of those four
paths; run it only on approval. If the push is rejected — usually a protected
current branch — fall back to a `shipd-gate-install` branch and a pull request
(`gh pr create --fill`), say so, and report the PR's full URL, never just its
number. Do **not** arm auto-merge there — whether the repository allows it is
step 4's setting; arm it (`gh pr merge --auto --squash --delete-branch`) only
once that step ran or auto-merge is already allowed, else say the PR waits for
a human merge. A declined commit leaves no review running until the files are
pushed — say so, and carry on to the settings.

## 4. Take consent once for the settings

Read the PR mode first: `python3 "$S/spec_status.py" config-show`. Where
`pr-mode = "draft"`, drop the auto-merge option and note that the draft flow
never arms auto-merge. Then ask **once**, in a turn carrying no other
load-bearing prose, over exactly these steps — each option naming its exact
command and, in plain words, what it changes on GitHub — plus "do none of them":

- **Require the check** — `python3 "$S/../../review/scripts/review_gate.py"
  protect`. Requires `semantic-review` on the default branch with conversation
  resolution, preserving existing protection fields, minimal where none exist.
- **Allow auto-merge** — `gh api -X PATCH repos/<nwo> -F allow_auto_merge=true`.
- **Strict verdicts (optional)** — `gh variable set SHIPD_GATE_FAIL_OPEN --body
  false`. State the trade-off: a review with no verdict marker then leaves the
  required check `pending` instead of passing fail-open — only worth taking
  alongside the reviewer token.

Recommend the first two; hand-offs are never choices. Declining runs nothing —
go straight to the token relay and the verification.

## 5. Run what was approved

Run each approved command exactly as shown, one at a time. All three need
admin permission: a denial is that step's failure, reported with the manual
hint — branch protection, pull-request settings, or Actions variables — and
never blocks the remaining approved steps. Never retry a denied call.

## 6. Hand off the reviewer token

Strictness needs `COPILOT_GITHUB_TOKEN`, and only a human can mint it. Relay
the recipe as prose: a **fine-grained** personal access token owned by the
account whose Copilot subscription pays for the reviews, **repository access:
none**, one account permission — **"Copilot Requests" → Read and write** — and
a bounded expiry. Hand over `gh secret set COPILOT_GITHUB_TOKEN --repo <nwo>`:
never run it, never read the token, never suggest a broader-scope one. Where
the user skips it, say the poll fallback authors no verdict marker, so the
check passes fail-open — the gate is **advisory until the secret exists**.

## 7. Verify, then report honestly

Run `shipd doctor` and read its `protection`, `automerge`, and
`copilot-secret` lines back verbatim as the evidence — never infer a setting's
state from a step you ran. Close with the verdict: what is installed, what is
required at merge time, strict or advisory, and the exact commands the user
still runs themselves. Add the note nothing here touches: asking for a review
is a GitHub-side setting — request Copilot per pull request, or a branch
ruleset for every one.

## Update — refresh an installed gate (`/s:gate update`)

Bring an already-gated repository's managed files to the running plugin
version and ship that refresh — nothing more. After step 1's preflight, read
the states from the bare `shipd copilot` report's `<state> <path> — <detail>`
lines, never re-derived from file contents. All four `installed` at this
version → report it current and stop: no write, no commit, no push. A
`foreign` path → stop naming the file; never `--force` on your own judgement.
Else run `shipd copilot add`, relay its report, commit exactly the four
managed paths, and push — the invocation is the consent. A rejected push falls
back to a `shipd-gate-update` branch and pull request with auto-merge
attempted (`gh pr merge --auto --squash --delete-branch`); report the full
URL, saying it awaits a human merge where arming is rejected. Close by
relaying the post-refresh state lines. No repository setting is touched — no
protection write, no auto-merge PATCH, no variable, no secret — and no consent
round, token hand-off, or doctor verification runs.
