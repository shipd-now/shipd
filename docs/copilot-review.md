<!-- doc-type: how-to -->

# Review gate

The review gate runs the [`/s:review`](semantic-review.md) review on every pull request, as a
GitHub Copilot agent skill that `shipd copilot` installs. A gate workflow turns the review into the
`semantic-review` commit status. A repository secret selects one of two reviewer modes, which the
[Review gate reference](copilot-review-reference.md) describes.

## When to use it

- Install the gate to have every pull request reviewed before it merges.
- Run `/s:review` alone for a review of local changes before a push.
- Add the spec lint action to keep a malformed spec off `main`.

## How to run it

### Before you start

- A **paid Copilot plan** — Pro, Pro+, Business, or Enterprise.
- The repository **hosted on GitHub**, with rights to push a branch.
- `shipd` on your PATH (see [getting started](getting-started.md#1-install)).

**In a Claude Code session, `/s:gate` runs this whole guide for you.** It preflights the
prerequisites, runs `shipd copilot add`, and offers to commit and push. It then takes one consent
round for the settings, relays the token recipe, and verifies with [`shipd doctor`](doctor.md).

### 1. Install the files

```
$ shipd copilot add
wrote .github/skills/code-review/SKILL.md
wrote .github/skills/code-review/scripts/semdiff.py
wrote .github/workflows/copilot-code-review.yml
wrote .github/workflows/copilot-review-gate.yml
Copilot code review reads these from a pull request's head branch.
```

The verb manages those four files alone. The
[reference](copilot-review-reference.md#the-managed-files) gives each file's role. Run the verb from
the repository you want reviewed, or pass `--root ~/code/some-repo` to install into another one.

### 2. Commit and push the files

```bash
git add .github/skills/code-review .github/workflows/copilot-*review*.yml
git commit -m "Install the shipd Copilot code-review skill"
git push
```

**Copilot reads skills and workflows from the pull request's head branch**, not from your working
tree and not from the base branch. Files that sit only on disk are invisible to the review.

### 3. Enable reviews

Installing the files makes the skill available. Asking for a review is a GitHub-side setting, which
`shipd copilot` never touches.

- **Per pull request.** Request **Copilot** as a reviewer from the Reviewers menu.
- **For every pull request.** Add a **branch ruleset** on the protected branch requiring Copilot
  code review, under **Settings** → **Rules** → **Rulesets**.

The poll fallback waits for that review. The CLI reviewer mode needs neither, as it reviews every
pull request from its own Actions job.

### 4. Set the reviewer token

`COPILOT_GITHUB_TOKEN` selects the CLI reviewer mode and must only spend Copilot requests.

**Create a dedicated token** under **Settings** → **Developer settings** → **Personal access
tokens** → **Fine-grained tokens** → **Generate new token**:

1. **Resource owner**: the account whose Copilot subscription pays.
2. **Repository access**: **none**. The reviewer needs no repository permission; the workflow's own
   token does every repository operation.
3. **Account permissions**: **"Copilot Requests"** → *Read and write*, and nothing else. Without it
   the CLI refuses to start.
4. **Expiration**: pick a bounded one, such as 90 days.

**Never reuse a broad-scope token.** Any workflow run in the repository can read its secrets, even
one an unread pull request adds. This token can do one thing if it leaks: spend Copilot credits.

**Store it as a repository secret.** Storing a secret needs **Secrets: read and write** on the
repository. That is a different credential from the reviewer token you store.

```bash
gh secret set COPILOT_GITHUB_TOKEN --repo <owner>/<repo>
```

- **Expiry is fail-safe.** An expired token stops the CLI: the gate posts no terminal status, and
  `semantic-review` stays `pending`, never green. To rotate, re-run `gh secret set` with a new one.
- **Removing the secret restores the poll fallback.** Run `gh secret delete COPILOT_GITHUB_TOKEN`,
  and the next run takes the poll path.
- **Let the CI reviewer approve.** The CLI reviewer submits `APPROVE` or `REQUEST_CHANGES` as
  `github-actions[bot]`. GitHub refuses that until the setting **Allow GitHub Actions to create and
  approve pull requests** is on. `actions_approval.py allow` sets it; bare, it only reads. Off, you
  get a comment.

### 5. Verify

`shipd doctor` reports the three GitHub-side settings, read-only, on these three lines.

| Check | `ok` when |
| --- | --- |
| `protection` | the default branch requires the `semantic-review` status context; without admin access, GitHub hides that detail, so `ok` says the branch is protected and the details need admin access |
| `automerge` | the repository allows auto-merge, so `gh pr merge --auto` can arm |
| `copilot-secret` | `COPILOT_GITHUB_TOKEN` is set, so runs take the CLI reviewer mode |

Each check warns rather than fails. `/s:doctor` turns the two settings warnings into consent-gated
fixes; a human mints the token, so `copilot-secret` is a hand-off. Next, run bare `shipd copilot`.
It changes nothing; the [reference](copilot-review-reference.md#report-states-and---force) explains
its four report states.

### 6. Upgrade and uninstall

- **To upgrade, run `add` again.** It is idempotent, and rewrites the files it owns at the current
  version. Run it after every `claude plugin update s@shipd` that moves the plugin version, then
  commit and push the refreshed files.
- **To pick up new gate behaviour, run `/s:gate update`.** It re-renders the files and any installed
  room wake set.
- **Edit the plugin's templates, not the installed copies.** `add` overwrites them.
- **To uninstall, run `shipd copilot remove`.** It deletes only the files it owns, prunes the empty
  skill directory, and succeeds when nothing is there. Commit and push the deletions, as on install.

### 7. Lint your specs in CI

The root `action.yml` is a composite GitHub Action that runs shipd's spec lint on **your**
repository. It lints the master library, then every in-flight change under your resolved `planned/`
directory. Any lint finding fails the step, so a malformed spec or delta never reaches `main`.

```yaml
on: { pull_request: {}, push: { branches: [main] } }
jobs:
  spec-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: shipd-now/shipd@main
```

Prefer a pinned ref, `shipd-now/shipd@<tag-or-sha>`, over `@main`. A pin to a release tag or commit
SHA keeps an engine change from moving your CI underneath you. The `path` input defaults to `.`; the
[reference](copilot-review-reference.md#the-spec-lint-action) describes it.

## Reference

- [Review gate reference](copilot-review-reference.md) — the reviewer modes, the verdict rules, the
  trust boundary, the limits, the report states, and the lint action's inputs
- [The semantic review](semantic-review.md) — what this review reads, and how it rates findings
- [The research report](../.shipd/research/copilot-code-review/report.md) behind this integration
