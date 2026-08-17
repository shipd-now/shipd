# The shipd review inside GitHub Copilot code review

`shipd copilot` installs the shipd semantic review into a repository as a
GitHub Copilot **agent skill**, so Copilot's own pull-request review runs the
same engine and the same rubric as `/s:review` — cohort by cohort, over a
syntax-aware structural diff, with a high/medium/low severity rubric and a
ship-it/fix-required verdict.

A fourth managed file — the gate workflow — turns that review into the
`semantic-review` commit status, so the same check `/s:review` posts is
satisfied without a session. It has two reviewer modes: with a
`COPILOT_GITHUB_TOKEN` secret it **runs the review itself** through headless
GitHub Copilot CLI, and without one it falls back to **waiting for GitHub's own
Copilot code review** and classifying whatever that wrote. See
[The merge gate](#3-the-merge-gate) and
[Scope and limits](#scope-and-limits).

## Prerequisites

- A **paid Copilot plan** — Pro, Pro+, Business, or Enterprise. Agent skills
  and MCP for Copilot code review became generally available on those plans on
  July 29, 2026.
- The repository is **hosted on GitHub**, and you can push a branch and open a
  pull request against it.
- `shipd` on your PATH (see the [quickstart](quickstart.md#1-install)).

Nothing else. The review runs on GitHub Actions runners, which already provide
`git` and Python 3 — all the engine needs.

**On a private repository, prefer the gate's CLI reviewer mode.** GitHub runs
its Copilot review in a dynamic Actions run that checks the repository out for
itself, and on a private repository that checkout has been observed to fail
(`repository not found`, on a private individual-account repo). When it fails,
nothing under `.github/skills` is on disk for the review: the skill never
loads, the review is Copilot's generic one, it carries no verdict marker, and
every review of that repository classifies by the
[strictness knob](#strictness-shipd_gate_fail_open) — by default **fail-open**,
`success` described as *no verdict marker was parsed*; with
`SHIPD_GATE_FAIL_OPEN=false`, a `semantic-review` left `pending` on every pull
request. Nothing here can fix that from the repository side; it is decided in
Copilot's own runner.

**The setup workflow is fail-soft about it.** `copilot-code-review.yml` checks
the repository out `continue-on-error`, and runs its `difft`/`ripgrep` installs
only where that checkout succeeded. So on a repository the review runner cannot
check out, the setup job **completes** with the installs skipped rather than
failing — which is what GitHub's PR-visible `ccr-setup-step-failure` notice
keys on — and the review is the same one that repository was already getting.
On a public repository the checkout succeeds and the toolchain lands exactly as
before.

That limit belongs to the [poll fallback mode](#the-poll-fallback-mode) alone.
The [CLI reviewer mode](#the-cli-reviewer-mode) is **unaffected on private
repositories**: it reviews from the gate's own Actions job, with the ordinary
`actions/checkout` and the workflow's own token, which checks a private
repository out normally. If you do stay on the poll fallback, open the Copilot
code review run's log once and confirm its checkout step succeeded; where it
did not, treat the session flow (`/s:review` plus `review_gate.py post`) as the
working gate and do not rely on the Copilot verdict.

## 1. Install the files

From the repository you want reviewed:

```bash
shipd copilot add
```

```
wrote .github/skills/code-review/SKILL.md
wrote .github/skills/code-review/scripts/semdiff.py
wrote .github/workflows/copilot-code-review.yml
wrote .github/workflows/copilot-review-gate.yml
Copilot code review reads these from a pull request's head branch. Enable automatic review with a GitHub branch ruleset.
```

Those four files are everything the verb manages, and it touches nothing else
— no network, no `gh`, no other path:

- **`.github/skills/code-review/SKILL.md`** — the review instructions Copilot
  loads: what to run, how to order the work, the severity rubric, and the
  verdict rule. The skill directory is named `code-review` because GitHub
  recommends that name to make sure Copilot code review reads the skill.
- **`.github/skills/code-review/scripts/semdiff.py`** — the review engine, a
  byte-identical copy of the one `/s:review` uses. Stdlib-only Python 3, and
  read-only: every subcommand it exposes to the review only reads the
  repository and shells out to `git`.
- **`.github/workflows/copilot-code-review.yml`** — the environment workflow
  for the review runner. It installs `difft` (difftastic) and `ripgrep` so the
  diff is syntax-aware and symbol lookups are fast. Both are optional; see
  [Scope and limits](#scope-and-limits).
- **`.github/workflows/copilot-review-gate.yml`** — the gate workflow. It
  produces the `semantic-review` commit status your branch protection
  requires: running the review itself through Copilot CLI where a secret
  configures that, and otherwise bridging GitHub's own Copilot review into it.
  See [The merge gate](#3-the-merge-gate).

To install into a repository you are not standing in, pass `--root`:

```bash
shipd copilot add --root ~/code/some-repo
```

### Commit and push them

```bash
git add .github/skills/code-review \
        .github/workflows/copilot-code-review.yml \
        .github/workflows/copilot-review-gate.yml
git commit -m "Install the shipd Copilot code-review skill"
git push
```

This step is not optional bookkeeping. **Copilot reads skills and workflows
from the pull request's head branch**, not from your working tree and not from
the base branch. Files that are only on disk are
invisible to the review. One useful consequence: a pull request that changes
the skill is reviewed by the changed skill.

## 2. Enable reviews

Installing the files makes the skill *available*. Asking for a review is a
GitHub-side setting — `shipd copilot` cannot and does not touch it.

**Per pull request.** Request **Copilot** as a reviewer from the pull
request's Reviewers menu, the same way you would request a person. Copilot
reviews that pull request once, picking up the skill from its head branch.

**Automatically, for every pull request.** Add a **branch ruleset** on the
protected branch requiring Copilot code review (repository **Settings** →
**Rules** → **Rulesets**). From then on Copilot reviews each pull request
targeting that branch without anyone asking.

This step is what the gate's **poll fallback** waits for. It is optional in the
gate's [CLI reviewer mode](#the-cli-reviewer-mode), which reviews every pull
request from its own Actions job without a review ever being requested — though
a repository is free to run both surfaces.

## 3. The merge gate

`.github/workflows/copilot-review-gate.yml` turns the review into a real
check. It posts the **`semantic-review`** commit status — the same context
`/s:review`'s poster (`review_gate.py post`) sets — so a branch protection
requiring `semantic-review` is satisfied by whichever of the two ran last, and
a pull request no longer waits forever at *"Expected — waiting for status to be
reported"*.

The gate has **two reviewer modes**, and one repository secret decides which
one a run takes:

| | [CLI reviewer](#the-cli-reviewer-mode) | [Poll fallback](#the-poll-fallback-mode) |
| --- | --- | --- |
| Selected by | a `COPILOT_GITHUB_TOKEN` secret | no secret |
| Who reviews | headless GitHub Copilot CLI, in the gate's own Actions job | GitHub's Copilot code review |
| Runs the shipd engine | **yes** | no — its bash tool is disabled |
| Verdict marker | authored by the reviewer | never authored today |
| The status you get | strict: `fix-required` really blocks | fail-open in practice |
| Private repositories | works | the skill never loads |
| What it costs | Copilot AI credits per review | runner minutes spent waiting |

Whichever mode runs, the gate posts `semantic-review` = `pending` on the head
commit **first** — before it checks anything out or installs anything — so a
review of an older commit never counts for a newer one, and a failure later in
the job leaves the required check reading *pending* rather than unreported.

### The CLI reviewer mode

Give the gate a `COPILOT_GITHUB_TOKEN` and it stops waiting for anyone: it runs
the shipd review itself, through GitHub Copilot CLI, on its own runner.

**Set the secret** — a dedicated, minimally scoped fine-grained personal access
token stored as `COPILOT_GITHUB_TOKEN`. That is a short job with a few sharp
edges, so it has [its own section below](#the-reviewer-token). Nothing else
changes: the same workflow file handles both modes, so there is nothing to
re-install after adding or removing the secret.

**What the job then does**, on every pull request opened, updated, or reopened:

1. Posts `semantic-review` = `pending` on the head commit.
2. Checks that commit out with its full history — the engine's diff uses
   merge-base semantics, so it needs the history behind both ends.
3. Installs `difft` and `ripgrep` for the engine, then the `@github/copilot`
   CLI itself (`npm install -g @github/copilot`).
4. Runs the CLI non-interactively under a **10-minute timeout**, with the
   secret in its environment and its tools enabled so it can execute the
   engine. The prompt does not restate the rubric: it points the CLI at the
   repository's own `.github/skills/code-review/SKILL.md` — the same contract
   GitHub's review surface reads — names the base and the reviewed commit,
   forbids the CLI from posting anything itself, and requires the verdict
   marker as the last line of its output.
5. Classifies the **last non-empty line** of what the CLI wrote, exactly as
   below, and posts the resulting `semantic-review` status. Because the CLI
   really did run the engine and really did author the marker, a `fix-required`
   verdict here **blocks the merge** — this is the strict mode.
6. Posts the review text as a pull-request comment, so a human reads whatever
   the gate just judged, whichever way it went — including the case where it
   parsed no verdict and [strict mode](#strictness-shipd_gate_fail_open) left
   the check `pending`.

Only the CLI's standard output is captured. Its run statistics (duration, AI
credits, tokens) go to standard error and stay in the job log, where they
belong — folded into the review they would be the last line, and the verdict
would be lost.

**A failed or timed-out run leaves `pending`.** If the CLI exits nonzero or
exceeds its timeout it judged nothing, so the gate posts no terminal status and
no comment: the `pending` from step 1 stands, exactly as a poll timeout does,
and `review_gate.py post` from a session is the manual out.

**Private repositories work.** This review runs in your repository's own Actions
job with the workflow's token, so the checkout that fails for GitHub's review
runner simply does not arise here.

**What it costs.** Copilot AI credits, per review, against your Copilot
subscription's monthly allowance — on the order of **ten credits** for a small
change (a measured run: 6.64 credits in 16 seconds), plus a couple of runner
minutes for the installs. One review per push: the concurrency group cancels
the run a new push supersedes, so a rapid-fire branch does not stack up reviews.

### The reviewer token

`COPILOT_GITHUB_TOKEN` is the one secret this integration asks for, and the
only thing it must be able to do is spend Copilot requests. Give it exactly
that and nothing else.

**Create a dedicated token.** **Settings** → **Developer settings** →
**Personal access tokens** → **Fine-grained tokens** → **Generate new token**:

1. **Resource owner**: the account whose Copilot subscription pays for the
   reviews.
2. **Repository access**: **none**. Not "all repositories", not "only select
   repositories" — the reviewer needs no repository permission at all. Every
   repository operation in the gate (the checkout, the status post, the
   comment) is done by the workflow's own `github.token`.
3. **Account permissions**: **"Copilot Requests"** → *Read and write*, and
   nothing else. That permission alone is what lets a token drive Copilot
   headlessly; without it the CLI refuses to start.
4. **Expiration**: pick a bounded one (90 days is a sensible default). See the
   rotation note below — an expired token here is fail-safe.

**Never reuse a broad-scope token.** Any workflow run in the repository can
read its secrets, so a token stored here is a token every future workflow —
including one added by a pull request you have not read closely — can use.
A `repo`-scoped classic token or a fine-grained token with write access to your
repositories would hand that reach to anything running in CI. The
repository-access-free token above can do exactly one thing if it leaks: spend
Copilot credits.

**Store it as a repository secret.**

```bash
gh secret set COPILOT_GITHUB_TOKEN --repo <owner>/<repo>
# paste the token at the prompt; it is never echoed
```

(Or repository **Settings** → **Secrets and variables** → **Actions** → **New
repository secret**.) Note that the identity running `gh secret set` needs
**Secrets: read and write** on the repository — that is the permission of
whoever manages the repository, a *different* credential from the reviewer
token being stored, which needs no repository access whatsoever.

**Expiry is fail-safe; rotate by updating the secret.** When the token expires,
the Copilot CLI refuses to start, the reviewer step exits nonzero, and the gate
posts no terminal status: `semantic-review` stays `pending` on every pull
request until you notice. An expired token can never turn into a passing check
— the failure mode is a blocked merge, not a green one. To rotate, generate a
new token the same way and re-run the same `gh secret set` command; no workflow
change and no re-install is needed.

**Removing the secret restores the poll fallback.** Delete
`COPILOT_GITHUB_TOKEN` (`gh secret delete COPILOT_GITHUB_TOKEN`) and the very
next run takes the [poll path](#the-poll-fallback-mode) instead — the workflow
branches on the secret's presence at run time.

**What it spends.** Reviews consume Copilot AI credits from the *token
owner's* subscription allowance, not the repository's: about **7 credits** for
a small change in the runs measured here. Budget it against the account that
owns the token, and remember that the concurrency group caps this at one review
per push.

### The poll fallback mode

With no secret configured, the gate waits for GitHub's own Copilot code review
of the head commit — polling the reviews API for it — and classifies whatever
that review's body says.

**Why it polls instead of waiting to be told.** Copilot submits its review from
inside a dynamic Actions run, using the workflow-scoped token, and GitHub does
not start workflow runs from events raised by such a token. So a
Copilot-authored review submission triggers **no `pull_request_review` run at
all** — measured twice on a dogfooding repository, against human reviews of the
same pull requests that triggered gate runs within three seconds. A gate that
only listened for that event posted `pending` and then never heard the one
thing it existed to hear. The `pull_request` run is the one that reliably
exists, so it is the one that waits: it polls the pull request's reviews
through the REST API for the newest review by
`copilot-pull-request-reviewer[bot]` whose `commit_id` is the head it was
triggered for. The review-event path is kept because it costs nothing and
still handles any submission GitHub does route.

**What this mode actually guarantees today: fail-open.** GitHub's Copilot code
review runs with its **bash tool disabled** and assembles the review body in
its own pipeline. The shipd engine therefore never executes there, and the
verdict marker is never authored — observed directly in a public-repository
run log. So a poll-mode `success` means *"Copilot reviewed this commit; no
verdict marker was parsed"*, not *"the review passed"*. The mode is worth
keeping — it costs nothing, needs no secret, and Copilot's own findings still
appear as a review on the pull request — but it is not a semantic gate. Where
you want the verdict to bind, use the CLI reviewer mode above, or post from a
session with `review_gate.py post`. That is also why the fail-open rule exists
at all: failing closed on a missing marker would brick every merge.

**The poll's bounds, and what a timeout means.** The poll runs every **20
seconds for at most 15 minutes**. On the dogfooding repository Copilot's
reviews landed two to three minutes after the request, so the window is
generous rather than tight. Each cycle also re-reads the pull request's own
head: once a new push has moved it, the poll exits quietly and that push's own
run — which has already posted its own `pending` — owns the gate from there.

If the window elapses with no Copilot review of that commit, the gate **leaves
the status `pending` and posts nothing further**. No review happened, so no
verdict is invented; a required `semantic-review` check simply stays unmet, and
the manual out is the session flow's poster, `review_gate.py post`. The same is
true if the poll is cancelled: the workflow keeps one concurrency group per
pull request with `cancel-in-progress`, so a new push cancels the poll it
supersedes.

**What it costs.** Waiting occupies a runner: up to 15 runner-minutes per pull
request update in the worst case, typically the two or three minutes until the
review lands. The concurrency group caps that at one live poll per pull
request, and public repositories bill nothing for it — on a private repository
those are billable Actions minutes.

### The verdict, in both modes

The reviewed text carries a machine-readable marker, which the skill instructs
the reviewer to emit as its last line. The gate reads **only that line** — it
takes the text's last non-empty line (carriage returns and surrounding
whitespace tolerated) and compares it for equality:

| The reviewed text's last non-empty line | Status posted |
| --- | --- |
| `<!-- shipd-verdict: fix-required -->` | `failure` — the merge is blocked. |
| `<!-- shipd-verdict: ship-it -->` | `success`. |
| *anything else* | `success`, described as *no verdict marker was parsed* — unless the repository [turned strictness on](#strictness-shipd_gate_fail_open), in which case nothing is posted and the check stays `pending`. |

**A marker quoted elsewhere in the text never counts.** A review that
*describes* the markers — a pull request installing this very skill draws
exactly that review — mentions both of them mid-text, and matching anywhere in
the body would read the quote as a verdict and fail a passing pull request.
Only the last line decides.

That last row is the **fail-open** rule. In CLI reviewer mode it is a
long-stop, for a review that came back malformed; in poll mode it is, today,
the outcome you should expect (see above). Either way a review that *did* run
the skill and found blocking problems posts `failure`.

In poll mode the gate acts only on a review whose author is
`copilot-pull-request-reviewer[bot]` and whose `commit_id` is the pull
request's current head: someone else's review, or Copilot's review of a
superseded commit, changes nothing. That holds on both of its paths — it is
what the poll searches for, and what the review event is guarded on.

### Strictness: `SHIPD_GATE_FAIL_OPEN`

Some repositories have ruled the opposite: a review that produced no verdict
must never green the required check, and a merge waiting on a human is the
correct outcome. That is one repository Actions variable, read by the gate at
classification time:

```bash
gh variable set SHIPD_GATE_FAIL_OPEN --body false
```

| `SHIPD_GATE_FAIL_OPEN` | A last line matching neither marker |
| --- | --- |
| unset (**the default**), or any value but `false` | `success`, described as *no verdict marker was parsed* — fail-open. |
| `false` | Nothing is posted. The `pending` from the run's first step stands and the run logs that no verdict was parsed. |

Strict mode changes **only** that case, and it changes it on every classify
path alike — the CLI reviewer's own output, a polled review, and a review
event. A real verdict still decides: `fix-required` posts `failure` and
`ship-it` posts `success` exactly as before.

**The manual out.** With the check left `pending`, a strict repository merges
by reviewing from a session and posting the status by hand — `/s:review`, then
`review_gate.py post` — or by pushing a commit whose review does end in a
marker.

**Pair the knob with the reviewer token.** Set the variable knowing that: on
the poll fallback, where the marker is
[never authored today](#the-poll-fallback-mode), `false` means *every*
Copilot-reviewed pull request stalls at `pending` and waits on that manual
session review. Strictness only pays for itself in
[CLI reviewer mode](#the-cli-reviewer-mode), where the marker is genuinely
produced and a missing one really is an anomaly — so configure
[the reviewer token](#the-reviewer-token) first, then turn the knob. In strict
mode that reviewer still posts the text it captured as a pull-request comment
even when it parsed no verdict, so the review you have to act on is on the
pull request rather than buried in a job log.

Set it as a **variable**, not by editing the installed workflow: `shipd copilot
add` reinstalls that file from the plugin's template and would revert a local
edit on the next upgrade. The variable outlives every upgrade.

### Tokens, permissions, and the session flow

The workflow does all its repository work with its own `github.token`
(`statuses: write` to post the status, `pull-requests: write` to poll the
reviews and to leave the review comment). The **only** secret it ever reads is
the optional `COPILOT_GITHUB_TOKEN`, and its value reaches nothing but the
Copilot CLI's own environment — never a `gh` call. Nothing here *asks* for a
Copilot review either; triggering that stays GitHub-side, per
[step 2](#2-enable-reviews).

**Coexisting with the session flow.** Running `/s:review` and posting the gate
from a Claude session writes the same `semantic-review` context on the same
commit. Neither poster excludes the other; the newest post on a commit is the
one the check reflects.

**Limit: pull requests from forks.** GitHub gives workflows triggered by a
fork's pull request a **read-only** token, so the gate cannot post a status
there and the check stays unreported — in either mode. Same-repository
branches — the shipd `change/<name>` flow — are unaffected. On a fork PR, post
the status from a session with `review_gate.py post`.

**Retracted: the "bootstrap" limit.** An earlier version of this guide warned
that the pull request installing the gate could not be bridged, on the belief
that a review-triggered workflow only ever runs from the default branch's copy
of the workflow file. Dogfooding disproved it: a gate workflow present only on
the head branch started runs for both of its triggers, on the installing pull
request itself. There is no bootstrap step — the pull request that installs
the gate is gated by the gate it installs, exactly like every later one. What
does not fire is a run for a *Copilot-authored* review submission, on any
branch, which is what the poll above exists to absorb.

## 4. Check and upgrade the install

Run the verb bare. It reports and changes nothing:

```bash
shipd copilot
```

```
copilot review skill in /Users/you/code/some-repo (this install: v0.6.127)
  installed .github/skills/code-review/SKILL.md — shipd-copilot v0.6.127
  installed .github/skills/code-review/scripts/semdiff.py — byte-identical to the plugin's engine
  installed .github/workflows/copilot-code-review.yml — shipd-copilot v0.6.127
  installed .github/workflows/copilot-review-gate.yml — shipd-copilot v0.6.127
`shipd copilot add` installs or refreshes those files; `shipd copilot remove` deletes the ones it owns.
Automatic review is enabled on GitHub, not here — add a branch ruleset requiring Copilot code review on the protected branch.
The Copilot code-review surface exposes no repository-side model selection, so nothing here pins a model.
```

(The version shown is whichever shipd plugin you have installed.)

Each managed file reports one of four states:

| State | Meaning |
| --- | --- |
| `installed` | Written by this shipd version — the marker matches, and `semdiff.py` is byte-identical to the plugin's engine. |
| `stale` | Written by an older shipd version, or a `semdiff.py` that has drifted from the plugin's copy. |
| `foreign` | The file exists but carries no `shipd-copilot` ownership marker — something other than this verb wrote it. |
| `absent` | Not installed. |

Ownership is decided by a marker line the templates carry: `<!-- shipd-copilot
v… -->` in `SKILL.md` and `# shipd-copilot v…` in each of the two workflows.
The installed `semdiff.py` has no marker of its own — it counts as owned
exactly when the `SKILL.md` beside it is owned.

**To upgrade, run `add` again.** It is idempotent: it rewrites the files it
owns at the current version, so a `stale` install becomes `installed` and an
already-current one is simply refreshed. Do this after every
`claude plugin update s@shipd` that moves the plugin version — then commit and
push the refreshed files, since the review only ever sees what is on the
branch.

Edit the plugin's templates rather than the installed copies. A re-`add`
overwrites them.

## 5. Uninstall

```bash
shipd copilot remove
```

```
removed .github/skills/code-review/SKILL.md
removed .github/skills/code-review/scripts/semdiff.py
removed .github/workflows/copilot-code-review.yml
removed .github/workflows/copilot-review-gate.yml
```

It deletes only the files it owns, prunes the `.github/skills/code-review`
directory tree once it is empty, and succeeds (saying `nothing to remove:`)
when there is nothing there — running it twice is fine. Commit the deletions and push, as with the
install.

## Foreign files and `--force`

If a managed path is `foreign`, both `add` and `remove` refuse, name the file,
and change nothing:

```
Error: .github/workflows/copilot-code-review.yml: not written by shipd copilot (no ownership marker) — pass --force to add it anyway
```

That is the guard against clobbering a `copilot-code-review.yml` your team
wrote by hand. When you have looked at the file and are content to lose it,
`--force` overrides:

```bash
shipd copilot add --force        # replace the foreign file with the shipd template
shipd copilot remove --force     # delete it along with the managed files
```

Everything else is refusal-by-default: without `--force`, no managed file is
written or deleted when any one of them is foreign.

## Scope and limits

- **The gate is the workflow's, not Copilot's.** Nothing in Copilot code
  review is documented to set a third-party commit status; a review only ever
  posts a review. What satisfies a required `semantic-review` check is the
  installed gate workflow posting the status from Actions — having either run
  the review itself or read GitHub's — so drop `copilot-review-gate.yml` and
  the Copilot run is once again purely advisory beside whatever check you
  require. Its fail-open rule means a `success` can also mean "reviewed, no
  verdict parsed"; the status description says which.
- **No repository-side model selection.** The Copilot code-review surface
  exposes no repository-side option to pin which model the review runs on, so
  nothing installed here configures one. This is documented rather than faked,
  and will be revisited if GitHub exposes a real option.
- **Skill pickup is relevance-driven.** GitHub loads skills under
  `.github/skills` when they are "relevant to the review". Naming the
  directory `code-review` is GitHub's own recommendation for making that
  likely, and it is what `add` installs — but there is no documented guarantee
  the skill runs on every single review. Expect a good hit rate, not
  determinism.
- **`difft` and `ripgrep` are optional.** Both workflows install them — the
  setup workflow for GitHub's review runner, the gate for its own CLI reviewer
  job — because they make the review sharper, not because the engine needs
  them.
  Without `difft` the engine falls back to its structural text engine and
  stamps `engine: "text"` on the affected entries (the skill tells the
  reviewer to say so in the review); without `ripgrep`, symbol lookup falls
  back to `git grep`. If the workflow fails or you drop it, the review still
  runs.
- **The review never writes.** The engine is read-only by construction and the
  skill instructs the reviewer not to edit the repository.

## See also

- [`/s:review`](../README.md#skills) — the same review, run locally against a
  base ref before you push.
- [`.shipd/research/copilot-code-review/report.md`](../.shipd/research/copilot-code-review/report.md)
  — the cited research this integration was designed from, including the
  GitHub sources for plan gating, the head-branch rule, and relevance-driven
  skill pickup.
