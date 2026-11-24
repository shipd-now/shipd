<!-- doc-type: how-to -->

# Give an agent its own GitHub account

A second GitHub account for a reviewer agent is optional. GitHub does not
count an author's approval of their own pull request. A reviewer on the
author's account therefore posts its review as a comment. A second account
lets the review count as an approval. This guide gives a reviewer agent a
second account and checks that the room sees it.

The `gh` CLI picks the account from the environment. shipd adds no key, flag,
or file for it. [Run agents in a pull request's room](room-run.md) covers the
room itself.

## When to use it

- When a review must count as a GitHub approval.
- When the repository sets `distinct_reviewer` to `true` in
  [`.shipd-config.json`](customise.md).

With `distinct_reviewer` set to `true`, a
[`shipd room run`](room-run.md) with role `reviewer` or `ci` on the author's
own account exits `1` with one `Error:` line. It posts nothing. Without it,
the run continues with one warning, and the review posts as a comment. An
author run on any other account only gets a warning.

## How to run it

### Before you start

- You own, or can create, a second GitHub account.
- The second account has write access to the repository.
- You have installed `gh` and run a session that reaches the repository.

A reviewer account that claims reviews needs push permission on the
repository; see [Review claims](room-review-claims.md).

### 1. Set up the second account

1. Sign in to GitHub as the second account.
2. Choose one credential for it:
   - A fine-grained token. Give it read and write access to pull requests
     and issues on the repository.
   - A `gh` config directory. Sign in to `gh` once with `GH_CONFIG_DIR`
     pointing at a new directory.
3. Keep the credential outside the repository, in your shell profile or a
   secret manager.

### 2. Start the reviewer session

1. Set the credential in the environment of the reviewer session only. Use a
   token:

   ```sh
   GH_TOKEN="$REVIEWER_TOKEN" claude
   ```

   Or use a config directory:

   ```sh
   GH_CONFIG_DIR="$HOME/.config/gh-reviewer" claude
   ```

2. Start the author's session without these variables. It keeps the shared
   `gh` login.

### 3. Verify the account

1. Run `whoami` from the reviewer session:

   ```sh
   shipd room whoami 412
   ```

2. Read the output. It names the login, the author, and the source:

   ```json
   {"login": "reviewer-b", "author": "mikkel", "source": "GH_TOKEN", "is_author": false, "may_approve": true}
   ```

   The `source` value names the first credential `gh` uses, in `gh`'s
   order. On `github.com` the order is `GH_TOKEN`, `GITHUB_TOKEN`,
   `GH_CONFIG_DIR`, then `gh-login`. A CI job that sets only `GITHUB_TOKEN`
   reports `GITHUB_TOKEN`. On a GitHub Enterprise Server host,
   `GH_ENTERPRISE_TOKEN` and `GITHUB_ENTERPRISE_TOKEN` take the place of the
   first two. The source never shows a token.

3. Check the exit code. `whoami` exits `1` with one `Error:` line when `gh`
   cannot read the login. A login that matches the author, ignoring case,
   prints `is_author` true and `may_approve` false, and exits `0`. With
   `distinct_reviewer` set to `true`, that login exits `1` instead. A GitHub
   App's `app/<slug>` and `<slug>[bot]` count as one account.

The [`/s:room`](multi-agent-pr.md) skill runs `whoami` before every approving
review and stops on the error. With `may_approve` false, the skill still
reviews, and the review posts as a comment. `shipd room join` with role
`reviewer` or `ci` warns on stderr when the login is the author's. It still
joins.

### Verify an author bot

An author session that runs on a GitHub App installation token (`GH_TOKEN`)
checks that it owns the pull request before it fixes a finding:

```sh
shipd room whoami 412 --author
```

GitHub refuses `gh api user` for an installation token, so `whoami` reads the
login from the GraphQL viewer instead. The verb exits `0` with `is_author`
true on the bot's own pull request and `1` with one `Error:` line otherwise.

### Keep the token out of the repository

- Never write a token into a tracked file.
- Never write a token into `.shipd-config.json`.
- Never pass a token as a command-line argument.

## Reference

- [Run agents in a pull request's room](room-run.md) — the room verbs and the
  listeners.
- [Multi-agent PR](multi-agent-pr.md) — the model.
- [Semantic review](semantic-review.md) — the gate that posts reviews.
- [Customising shipd](customise.md) — the `distinct_reviewer` key.
