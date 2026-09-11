<!-- doc-type: how-to -->

# Install the Copilot review gate

`shipd copilot` installs the shipd semantic review into a repository as a
GitHub Copilot agent skill. A gate workflow turns that review into the
`semantic-review` commit status. [Copilot review
reference](copilot-review-reference.md) covers the two reviewer modes, the
verdict rules, the trust boundary, and the limits.

## Prerequisites

- A **paid Copilot plan** — Pro, Pro+, Business, or Enterprise.
- The repository **hosted on GitHub**, with rights to push a branch.
- `shipd` on your PATH (see [getting started](getting-started.md#1-install)).

**In a Claude Code session, `/s:gate` runs this whole guide for you.** It
preflights the prerequisites, runs `shipd copilot add`, and offers to commit
and push. It then takes one batched consent round over the repository settings,
relays the token recipe, and verifies with `shipd doctor`. Read on to set the
gate up by hand.

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
Copilot code review reads these from a pull request's head branch.
```

Those four files are everything the verb manages. The
[reference](copilot-review-reference.md#the-managed-files) gives each file's
role. Pass `--root ~/code/some-repo` to install into a repository you are not
standing in.

## 2. Commit and push the files

```bash
git add .github/skills/code-review .github/workflows/copilot-*review*.yml
git commit -m "Install the shipd Copilot code-review skill"
git push
```

This step is not bookkeeping. **Copilot reads skills and workflows from the
pull request's head branch**, not from your working tree and not from the base
branch. Files that sit only on disk are invisible to the review.

One consequence lands on GitHub's review, and so on the gate's poll fallback:
the changed skill reviews the pull request that changes it. That is convenient
while you iterate on the rubric. It does not hold in CLI reviewer mode, which
pins the instructions to the base ref.

## 3. Enable reviews

Installing the files makes the skill available. Asking for a review is a
GitHub-side setting, which `shipd copilot` never touches.

- **Per pull request.** Request **Copilot** as a reviewer from the pull
  request's Reviewers menu, as you would request a person.
- **For every pull request.** Add a **branch ruleset** on the protected branch
  requiring Copilot code review, under **Settings** → **Rules** → **Rulesets**.

The gate's poll fallback waits for that review. The CLI reviewer mode needs
neither path, because it reviews every pull request from its own Actions job.

## 4. Set the reviewer token

`COPILOT_GITHUB_TOKEN` selects the CLI reviewer mode, and the only thing it
must do is spend Copilot requests. Give it exactly that.

**Create a dedicated token** under **Settings** → **Developer settings** →
**Personal access tokens** → **Fine-grained tokens** → **Generate new token**:

1. **Resource owner**: the account whose Copilot subscription pays.
2. **Repository access**: **none**. The reviewer needs no repository
   permission; the workflow's own token does every repository operation.
3. **Account permissions**: **"Copilot Requests"** → *Read and write*, and
   nothing else. Without it the CLI refuses to start.
4. **Expiration**: pick a bounded one, such as 90 days.

**Never reuse a broad-scope token.** Any workflow run in the repository can
read its secrets, including a run some unread pull request adds. The token
above can do one thing if it leaks: spend Copilot credits.

**Store it as a repository secret.**

```bash
gh secret set COPILOT_GITHUB_TOKEN --repo <owner>/<repo>
```

Storing a secret needs **Secrets: read and write** on the repository. That is a
different credential from the reviewer token you store.

**Expiry is fail-safe.** An expired token stops the CLI, so the gate posts no
terminal status and `semantic-review` stays `pending`. An expired token can
never green a check. To rotate, mint a new one and re-run `gh secret set`.

**Removing the secret restores the poll fallback.** Run
`gh secret delete COPILOT_GITHUB_TOKEN`, and the next run takes the poll path.

## 5. Verify

`shipd doctor` reads the three GitHub-side settings, read-only, and reports
them as its last three lines.

| Check | `ok` when |
| --- | --- |
| `protection` | the default branch requires the `semantic-review` status context |
| `automerge` | the repository allows auto-merge, so `gh pr merge --auto` can arm |
| `copilot-secret` | `COPILOT_GITHUB_TOKEN` is set, so runs take the CLI reviewer mode |

Each check warns rather than fails. `/s:doctor` turns the two settings warnings
into consent-gated fixes; the `copilot-secret` one is a hand-off, because a
human mints the token. Then run the verb bare, which changes nothing:

```bash
shipd copilot
```

The [reference](copilot-review-reference.md#report-states-and---force) explains
the four states it reports.

## 6. Upgrade and uninstall

- **To upgrade, run `add` again.** It is idempotent, and rewrites the files it
  owns at the current version. Run it after every `claude plugin update
  s@shipd` that moves the plugin version, then commit and push the refreshed
  files.
- **Edit the plugin's templates, never the installed copies.** A re-`add`
  overwrites them.
- **To uninstall, run `shipd copilot remove`.** It deletes only the files it
  owns, prunes the empty skill directory, and succeeds when nothing is there.
  Commit the deletions and push, as with the install.

## See also

- [`/s:review`](../README.md#skills) — the same review, run locally against a
  base ref before you push.
- [`.shipd/research/copilot-code-review/report.md`](../.shipd/research/copilot-code-review/report.md)
  — the cited research behind this integration.
