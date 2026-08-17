# The shipd review inside GitHub Copilot code review

`shipd copilot` installs the shipd semantic review into a repository as a
GitHub Copilot **agent skill**, so Copilot's own pull-request review runs the
same engine and the same rubric as `/s:review` — cohort by cohort, over a
syntax-aware structural diff, with a high/medium/low severity rubric and a
ship-it/fix-required verdict.

The result posts as a Copilot review on the pull request, and a fourth managed
file — the gate workflow — bridges its verdict into the `semantic-review`
commit status, so the same check `/s:review` posts is satisfied by Copilot's
run. See [The merge gate](#3-the-merge-gate) and
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

**On a private repository, verify the review runner's checkout once.** Copilot
runs its review in a dynamic Actions run that checks the repository out for
itself, and on a private repository that checkout has been observed to fail
(`repository not found`, on a private individual-account repo). When it fails,
nothing under `.github/skills` is on disk for the review: the skill never
loads, the review is Copilot's generic one, it carries no verdict marker, and
every review of that repository classifies **fail-open** — `success`,
described as *no verdict marker was parsed*. Nothing here can fix that from
the repository side; it is decided in Copilot's own runner. So on the first
review, open the Copilot code review run's log and confirm its checkout step
succeeded. Where it does not, treat the session flow (`/s:review` plus
`review_gate.py post`) as the working gate and do not rely on the Copilot
verdict.

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
  posts the `semantic-review` commit status, bridging Copilot's submitted
  review into the check your branch protection requires. See
  [The merge gate](#3-the-merge-gate).

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

## 3. The merge gate

`.github/workflows/copilot-review-gate.yml` turns the review into a real
check. It posts the **`semantic-review`** commit status — the same context
`/s:review`'s poster (`review_gate.py post`) sets — so a branch protection
requiring `semantic-review` is satisfied by whichever of the two ran last, and
a pull request no longer waits forever at *"Expected — waiting for status to be
reported"*.

Two triggers, one job:

| Event | What the gate does |
| --- | --- |
| A pull request **opens**, **updates** (a new push), or **reopens** | Posts `pending` on the new head commit — a review of an older commit never counts for a newer one — and then **waits for Copilot's review of that commit**, polling for it, and posts the verdict it finds. |
| Copilot **submits a review** of the current head commit, through an event GitHub routes | Posts the verdict straight from the event's review body. |

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

The review body carries a machine-readable marker, which the skill instructs
the reviewer to emit as the body's last line. The gate reads **only that
line** — it takes the body's last non-empty line (carriage returns and
surrounding whitespace tolerated) and compares it for equality:

| The body's last non-empty line | Status posted |
| --- | --- |
| `<!-- shipd-verdict: fix-required -->` | `failure` — the merge is blocked. |
| `<!-- shipd-verdict: ship-it -->` | `success`. |
| *anything else* | `success`, described as *no verdict marker was parsed*. |

**A marker quoted elsewhere in the body never counts.** A review that
*describes* the markers — a pull request installing this very skill draws
exactly that review — mentions both of them mid-text, and matching anywhere in
the body would read the quote as a verdict and fail a passing pull request.
Only the last line decides.

That last row is the **fail-open** rule, and it is deliberate. Skill pickup is
relevance-driven (see [Scope and limits](#scope-and-limits)), so a Copilot
review that ignored the skill produces no marker — failing closed there would
brick every merge on a Copilot miss. A review that *did* run the skill and
found blocking problems still posts `failure`.

The gate only acts on a review whose author is
`copilot-pull-request-reviewer[bot]` and whose `commit_id` is the pull
request's current head: someone else's review, or Copilot's review of a
superseded commit, changes nothing. That holds on both paths — it is what the
poll searches for, and what the review event is guarded on.

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

The workflow authenticates with its own `github.token` (with `statuses: write`
to post and `pull-requests: read` to poll) and needs no secret of yours. It
also never *asks* for a review — triggering stays GitHub-side, per
[step 2](#2-enable-reviews).

**Coexisting with the session flow.** Running `/s:review` and posting the gate
from a Claude session writes the same `semantic-review` context on the same
commit. Neither poster excludes the other; the newest post on a commit is the
one the check reflects.

**Limit: pull requests from forks.** GitHub gives workflows triggered by a
fork's pull request a **read-only** token, so the gate cannot post a status
there and the check stays unreported. Same-repository branches — the shipd
`change/<name>` flow — are unaffected. On a fork PR, post the status from a
session with `review_gate.py post`.

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
  review is documented to set a third-party commit status; the review itself
  still only posts a review. What satisfies a required `semantic-review` check
  is the installed gate workflow reading that review and posting the status
  from Actions — so drop `copilot-review-gate.yml` and the Copilot run is once
  again purely advisory beside whatever check you require. Its fail-open rule
  means a `success` can also mean "reviewed, no verdict parsed"; the status
  description says which.
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
- **`difft` and `ripgrep` are optional.** The workflow preinstalls them
  because they make the review sharper, not because the engine needs them.
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
