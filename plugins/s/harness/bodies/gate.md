<!-- description: Set up the shipd semantic review gate in a repository, taking consent before anything changes on GitHub. -->
# /s:gate — install the review gate, with consent

Run the existing engines in order: install the files, commit them, require the
check, hand off the reviewer token, verify. Invent no mechanism, and change
nothing the user did not approve. One setup round per invocation.

<!-- include:preamble -->

## 1. Preflight

Confirm all three before writing anything, **in this order**: the working
directory is a git repository (`git rev-parse --show-toplevel`), `gh` is
authenticated (`gh auth status`), and a GitHub repository resolves
(`gh repo view --json nameWithOwner` — keep the `<nwo>`). `gh repo view` cannot
succeed unauthenticated, so checking it first would mask a missing login as a
missing repository. If any fails, report what is missing, run no
install and no mutation, and stop. A missing `gh` is an install command for the
user; an unauthenticated one is `gh auth login` — interactive, so hand it over
rather than running it.

## 2. Install the four files

Run `shipd copilot add` and relay its per-file report verbatim. It is offline,
idempotent, and touches exactly `.github/skills/code-review/SKILL.md`, that
directory's `scripts/semdiff.py`, `.github/workflows/copilot-code-review.yml`,
and `.github/workflows/copilot-review-gate.yml`. If it refuses because a
managed path is foreign, report the file it named and stop — never pass
`--force` on your own judgement.

## 3. Commit and push them

Copilot reads skills and workflows from the pull request's **head branch**, so
files left on disk are invisible to the review. Propose the commit and push of
those four paths, and run it only on approval. If the push is rejected — the
usual cause is a protected current branch — fall back to a
`shipd-gate-install` branch and a pull request (`gh pr create --fill`), say
that is what happened, and report the pull request's full URL, never just its
number. Do **not** arm auto-merge there: whether the repository allows it is the
setting step 4 offers. Arm it (`gh pr merge --auto --squash --delete-branch`)
only afterwards, once that step ran or auto-merge is already allowed; otherwise
say the pull request waits for a human merge. If the user declines the commit,
say plainly that no review runs until the files are pushed, and carry on — the
settings are still worth setting.

## 4. Take consent once for the settings

Read the PR mode first: `python3 "$S/spec_status.py" config-show`. Where
`pr-mode = "draft"`, drop the auto-merge option and note that the draft flow
never arms auto-merge. Then ask **once**, in a turn carrying no other
load-bearing prose, over exactly these steps — each option naming its exact
command and, in plain words, what it changes on GitHub — plus "do none of them":

- **Require the check** — `python3 "$S/../../review/scripts/review_gate.py"
  protect`. Requires `semantic-review` on the default branch with conversation
  resolution, preserving every protection field already there and creating the
  minimal protection where the branch has none.
- **Allow auto-merge** — `gh api -X PATCH repos/<nwo> -F allow_auto_merge=true`.
- **Strict verdicts (optional)** — `gh variable set SHIPD_GATE_FAIL_OPEN --body
  false`. State the trade-off: a review with no verdict marker then leaves the
  required check `pending` instead of passing fail-open, which is only worth
  taking alongside the reviewer token.

Recommend the first two. Hand-offs are never choices. Declining runs nothing:
go straight to the token relay and the verification.

## 5. Run what was approved

Run each approved command exactly as shown, one at a time. All three need admin
permission: a denial is reported as that step's failure with the manual hint —
the branch protection settings, the repository's pull-request settings, or its
Actions variables — and never blocks the remaining approved steps. Never retry
a denied call.

## 6. Hand off the reviewer token

Strictness needs `COPILOT_GITHUB_TOKEN`, and only a human can mint it. Relay
the recipe as prose: a **fine-grained** personal access token owned by the
account whose Copilot subscription pays for the reviews, with **repository
access: none**, exactly one account permission — **"Copilot Requests" → Read
and write** — and a bounded expiry. Then hand over
`gh secret set COPILOT_GITHUB_TOKEN --repo <nwo>`: never run it, never read the
token, never suggest a broader-scope one. Where the user skips it, say what
that leaves — the gate polls GitHub's own Copilot review, which authors no
verdict marker today, so the check passes fail-open and the gate is **advisory
until the secret exists**.

## 7. Verify, then report honestly

Run `shipd doctor` and read its `protection`, `automerge`, and
`copilot-secret` lines back verbatim as the evidence of what was set up — never
infer a setting's state from a step you ran. Close with the verdict: what is
installed, what is required at merge time, whether the gate is strict or
advisory, and the exact commands the user still has to run themselves. Add the
one note nothing here touches: asking for a review is a GitHub-side setting —
request Copilot per pull request, or add a branch ruleset requiring Copilot code
review for every one.
