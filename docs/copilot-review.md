# The shipd review inside GitHub Copilot code review

`shipd copilot` installs the shipd semantic review into a repository as a
GitHub Copilot **agent skill**, so Copilot's own pull-request review runs the
same engine and the same rubric as `/s:review` — cohort by cohort, over a
syntax-aware structural diff, with a high/medium/low severity rubric and a
ship-it/fix-required verdict.

The result is **advisory**. It posts as a Copilot review on the pull request
and blocks nothing; if your repository requires the `semantic-review` status
check, that check stays the merge gate. See
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

## 1. Install the files

From the repository you want reviewed:

```bash
shipd copilot add
```

```
wrote .github/skills/code-review/SKILL.md
wrote .github/skills/code-review/scripts/semdiff.py
wrote .github/workflows/copilot-code-review.yml
Copilot code review reads these from a pull request's head branch. Enable automatic review with a GitHub branch ruleset.
```

Those three files are everything the verb manages, and it touches nothing else
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

To install into a repository you are not standing in, pass `--root`:

```bash
shipd copilot add --root ~/code/some-repo
```

### Commit and push them

```bash
git add .github/skills/code-review .github/workflows/copilot-code-review.yml
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

## 3. Check and upgrade the install

Run the verb bare. It reports and changes nothing:

```bash
shipd copilot
```

```
copilot review skill in /Users/you/code/some-repo (this install: v0.6.123)
  installed .github/skills/code-review/SKILL.md — shipd-copilot v0.6.123
  installed .github/skills/code-review/scripts/semdiff.py — byte-identical to the plugin's engine
  installed .github/workflows/copilot-code-review.yml — shipd-copilot v0.6.123
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
v… -->` in `SKILL.md` and `# shipd-copilot v…` in the workflow. The installed
`semdiff.py` has no marker of its own — it counts as owned exactly when the
`SKILL.md` beside it is owned.

**To upgrade, run `add` again.** It is idempotent: it rewrites the files it
owns at the current version, so a `stale` install becomes `installed` and an
already-current one is simply refreshed. Do this after every
`claude plugin update s@shipd` that moves the plugin version — then commit and
push the refreshed files, since the review only ever sees what is on the
branch.

Edit the plugin's templates rather than the installed copies. A re-`add`
overwrites them.

## 4. Uninstall

```bash
shipd copilot remove
```

```
removed .github/skills/code-review/SKILL.md
removed .github/skills/code-review/scripts/semdiff.py
removed .github/workflows/copilot-code-review.yml
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

- **Advisory, not a gate.** Copilot posts its own review on the pull request.
  Nothing in Copilot code review is documented to set a third-party commit
  status, so it does not set — or satisfy — the required `semantic-review`
  check that `review_gate.py` drives. Treat the Copilot run as a second opinion beside
  the required gate, not as a replacement for it.
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
