---
name: copilot
description: >-
  Set up the shipd semantic review gate in a repository end to end: preflight
  the prerequisites, install the four managed files with `shipd copilot add`,
  commit and push them, then — on consent — require the `semantic-review`
  check, enable auto-merge, hand off the reviewer token, and verify with
  `shipd doctor`. Use when asked to set up Copilot review, install the review
  gate, block PRs on the semantic review, or turn on the merge gate. Trigger
  phrases: "set up copilot review", "install the review gate", "copilot code
  review", "block PRs on review", "/s:copilot".
---

# /s:copilot — install the review gate, with consent

You are the **setup layer over the shipd Copilot review integration**. The
pieces already exist — `shipd copilot add` writes the files, `review_gate.py
protect` requires the check, `shipd doctor` reads the settings back. Your job
is to run them in the right order, take explicit consent before anything
changes, hand the interactive steps to the user, and finish with an honest
account of what is gated and what is not.

**You invent no mechanism.** Every install, protection write, and verification
in this flow is an existing engine command named below. You never hand-edit an
installed file, never compose a protection body of your own, and never extend
`shipd doctor`.

**You never change anything the user did not consent to.** No commit, no push,
no branch-protection write, no repository setting changes before a consent
answer that names it.

**The goal, stated honestly.** What the user wants is: a PR carrying a
`fix-required` verdict is blocked, and a `ship-it` one merges. That holds only
with **both** the branch protection *and* the CLI reviewer token
(`COPILOT_GITHUB_TOKEN`). Without the token the gate falls back to polling
GitHub's own Copilot review, which authors no verdict marker today, so the
check is **fail-open advisory**. Say so plainly wherever it applies; never
report a repository as gated when it only has half of the pair.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include
`shipd:copilot v<version>` in your first user-visible status sentence (e.g.
"shipd:copilot v0.6.144 — preflighting the repository"), so the user can see
which plugin snapshot the session is running.

**One setup round per invocation.** Preflight → install → commit → consent →
apply → verify, and stop. A step that fails is reported with its manual hint;
you never loop, retry, or escalate to a second round.

## 1. Resolve the binary

Resolve the `shipd` binary in this order and use the first that exists:

1. `shipd` on `PATH` — the consumer launcher (`command -v shipd`).
2. `${CLAUDE_PLUGIN_ROOT}/bin/shipd` — the checkout or cache-snapshot copy.

If neither resolves, report that the `shipd` binary cannot be found, name both
locations you tried, and stop. Do not install a launcher.

## 2. Preflight

Three prerequisites, checked before anything is written:

| Check | How | Failure |
| --- | --- | --- |
| A git repository | `git rev-parse --show-toplevel` | Report that the working directory is not a git repository and stop. |
| `gh` authenticated | `command -v gh`, then `gh auth status` | Report what is missing and stop. |
| A GitHub remote | `gh repo view --json nameWithOwner` | Report that no GitHub repository resolves here and stop. Keep the `<nwo>` it printed — every later step names it. |

Check them **in that order**: `gh repo view` cannot succeed unauthenticated, so
running it first would report a missing repository when the real cause is a
missing login.

**Both `gh` failures are hand-offs, never fixes.** If `gh` is not on PATH, name
the install command for the platform and stop. If it is present but not
authenticated, hand the login to the user:

```
! gh auth login
```

Do not run it — it is interactive. **On any preflight failure, run no install
and no mutation**: stop with what is missing and the exact command the user
runs themselves.

## 3. Install the four managed files

```
<shipd> copilot add
```

The verb is offline and touches exactly four paths — it never calls `gh` and
never reaches the network:

```
.github/skills/code-review/SKILL.md
.github/skills/code-review/scripts/semdiff.py
.github/workflows/copilot-code-review.yml
.github/workflows/copilot-review-gate.yml
```

**Relay the verb's own report** — its per-file `wrote`/state lines, verbatim.
It is idempotent: a repeat run refreshes what it owns and upgrades a stale
install.

If it **refuses** because a managed path is foreign (a file at one of those
paths without the shipd ownership marker), report the file it named and stop.
Do not pass `--force` on your own judgement — that overwrites a file somebody
else wrote. Offer it as a choice only if the user asks to proceed, and say what
it replaces.

## 4. Commit and push them

Copilot reads skills and workflows **from the pull request's head branch**, so
files that only exist on disk are invisible to the review. Propose the commit
and push, and run it only on the user's approval:

```bash
git add .github/skills/code-review \
        .github/workflows/copilot-code-review.yml \
        .github/workflows/copilot-review-gate.yml
git commit -m "Install the shipd Copilot code-review skill"
git push
```

**If the push is rejected** — the usual cause is that the current branch is
protected against direct pushes — fall back to a branch and a pull request, and
say that is what happened:

```bash
git switch -c shipd-copilot-install
git push -u origin shipd-copilot-install
gh pr create --fill
```

**The fallback stops at the pull request — it does not arm auto-merge here.**
Whether the repository allows auto-merge at all is the setting step 5 offers, so
arming it now would fail on exactly the repositories that need the setting.
Report the PR's **full URL**, never just the number, and carry the PR forward:

- If the auto-merge step ran in step 6 (or `shipd doctor` already reports
  auto-merge allowed), arm it on that PR afterwards:
  `gh pr merge --auto --squash --delete-branch <pr>`.
- Otherwise — the user declined the setting, it failed, or `pr-mode: draft`
  dropped it — say the PR waits for a human merge, and report its full URL in
  the closing account.

If the user declines the commit, say plainly that the files are on disk only
and no review will run until they are committed and pushed, then carry on to
step 5 — the repository settings are still worth setting.

## 5. One consent round for the repository settings

First read the PR mode, since it decides whether one of the options exists at
all:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" config-show
```

The verb prints each declared key as `<key> = <json>  [<source>]`. **`pr-mode =
"draft"`** → omit the auto-merge option entirely and note that the draft flow
never arms auto-merge, so the setting buys nothing here. No `pr-mode` line, or
any other value → keep it.

Then collect consent in **one batched selection** over exactly these runnable
steps:

| Step | Command | What it changes |
| --- | --- | --- |
| Require the check | `python3 "${CLAUDE_PLUGIN_ROOT}/skills/review/scripts/review_gate.py" protect` | Requires the `semantic-review` status context on the default branch and turns on conversation resolution. Preserves every protection field the branch already has; creates the minimal protection when the branch has none. |
| Allow auto-merge | `gh api -X PATCH repos/<nwo> -F allow_auto_merge=true` | Lets `gh pr merge --auto` arm on this repository. **Omitted under `pr-mode: draft`.** |
| Strict verdicts (optional) | `gh variable set SHIPD_GATE_FAIL_OPEN --body false` | A review that produces no verdict marker then posts nothing and the required check stays `pending`, instead of passing fail-open. |

Honor the dialog-and-prose-separation rule:

- If the round needs a substantive brief — more than a one-line lead-in —
  **end that turn as plain text**: the steps, the exact command each runs, and
  the choices as a numbered list with the recommended default named, answered
  by a typed reply.
- Otherwise issue a **single question dialog in a prose-free turn**:
  multi-select over the steps, one option per step carrying the exact command
  and, in plain words, the change it makes on GitHub, plus a "Do none of them"
  option. No load-bearing prose outside the dialog.

**Recommend the first two, not the third.** `protect` and auto-merge are what
the gate needs to bite. `SHIPD_GATE_FAIL_OPEN=false` is worth taking **only
alongside the reviewer token** — on the poll fallback, where no marker is ever
authored, it leaves `semantic-review` `pending` on every pull request until a
session posts the gate by hand. State that trade-off in its option.

**The hand-offs are never dialog options.** `gh auth login` and
`gh secret set COPILOT_GITHUB_TOKEN` are prose in the report — there is nothing
here to consent to.

**Declining runs nothing.** If the user selects "Do none of them" (or declines
every step), perform no protection write, no repository PATCH, and no variable
set. Go straight to steps 7 and 8: the token hand-off, then the closing
`shipd doctor` verification — with the manual hints for the steps not taken.

## 6. Run only the consented steps

Run each approved command exactly as it was shown, one at a time, and capture
its exit code and output.

**All three need admin permission on the repository.** A denial (`HTTP 403`, or
a message naming a missing admin right) is reported as *that step's* failure
with the manual hint — the branch's protection settings, the repository's
**Settings → General → Pull Requests** checkbox, or **Settings → Secrets and
variables → Actions → Variables** — and it **never blocks the remaining
consented steps**. Never retry a denied call.

## 7. Hand off the reviewer token

This is the half that makes the gate strict, and it cannot be automated: the
token must be minted by a human, and the command that stores it prompts. Relay
the recipe **as prose, never as a dialog option** — a dedicated **fine-grained**
personal access token:

1. **Resource owner**: the account whose Copilot subscription pays for the
   reviews.
2. **Repository access**: **none**. The reviewer needs no repository permission
   at all; everything the gate does against the repository uses the workflow's
   own token.
3. **Account permissions**: **"Copilot Requests" → Read and write**, and
   nothing else. Without it the Copilot CLI refuses to start.
4. **Expiration**: bounded — 90 days is a sensible default. Expiry is fail-safe:
   the gate posts no terminal status, so the check stalls rather than greening.

Then hand over the storage step:

```
! gh secret set COPILOT_GITHUB_TOKEN --repo <nwo>
```

**Never run it**, never read the token, and never suggest a broader-scope one —
any workflow in the repository can read its secrets, so a `repo`-scoped token
stored here would hand that reach to everything in CI.

**Where the user skips it, say what that leaves.** The gate stays on the poll
fallback: it waits for GitHub's own Copilot review and classifies what that
wrote, which authors no verdict marker today, so `semantic-review` passes
fail-open. The gate is **advisory until the secret exists**. State that in the
closing report, not only here.

## 8. Verify with the preflight

Close by running the read-only preflight and reading back the three GitHub-side
check lines it prints — select them **by check name**, not by position; the
output ends with a `doctor: N problem(s)` summary line:

```
<shipd> doctor
```

Report the `protection`, `automerge`, and `copilot-secret` lines verbatim as
the verification of what was set up:

- `protection` — whether the default branch now requires `semantic-review`.
- `automerge` — whether auto-merge is allowed (waived under `pr-mode: draft`).
- `copilot-secret` — `warn` here is the fail-open fallback naming itself: the
  gate is installed without the reviewer token.

**Never infer a setting's state from a step you ran** — these lines are the
evidence. If the preflight output cannot be parsed into
`ok|warn|fail <check> — <detail>` lines, report exactly what you got and say
the verification could not be read.

## Enabling reviews is a GitHub-side setting

Installing the files makes the skill available; asking for a review is separate,
and nothing here touches it. Report it as a note, not a step:

- **Per pull request** — request **Copilot** as a reviewer from the Reviewers
  menu.
- **For every pull request** — add a branch ruleset requiring Copilot code
  review (**Settings → Rules → Rulesets**).

This is what the poll fallback waits for. In CLI reviewer mode the gate reviews
every pull request from its own Actions job, so it is optional there.

## Question rejection recovery

**Question rejection recovery.** A known Claude Code bug can deliver an
AskUserQuestion interaction as a tool rejection ("The user doesn't want
to proceed with this tool use") even when the user tried to answer.
Never treat a rejected or interrupted AskUserQuestion as a decline, a
stop, or an answer. When the user's next message arrives: if it answers
the pending question, fold it in and continue; otherwise re-offer the
same choices as a plain-text numbered list and wait for a typed reply.
Only an explicitly selected or typed stop/decline ends the flow.

## End

Close with the verdict in a line or two: what is installed, what is required at
merge time, whether the gate is strict or advisory, and the exact commands the
user still has to run themselves. Then stop.
