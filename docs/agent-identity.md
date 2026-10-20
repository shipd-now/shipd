<!-- doc-type: how-to -->

# Give an agent its own GitHub account

GitHub does not count an author's approval of their own pull request. An
agent that shares the author's `gh` login is the same person to GitHub, so
its approval never counts. This guide gives a reviewer agent a second
account and checks that the room sees it.

The `gh` CLI picks the account from the environment. shipd adds no key, flag,
or file for it. [Run an agent's turn in a multi-agent PR](pr-room.md) covers
the room itself.

## Before you start

- You own, or can create, a second GitHub account.
- The second account has write access to the repository.
- You have installed `gh` and run a session that reaches the repository.

## Set up the second account

1. Sign in to GitHub as the second account.
2. Choose one credential for it:
   - A fine-grained token. Give it read and write access to pull requests
     and issues on the repository.
   - A `gh` config directory. Sign in to `gh` once with `GH_CONFIG_DIR`
     pointing at a new directory.
3. Keep the credential outside the repository, in your shell profile or a
   secret manager.

## Start the reviewer session

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

## Verify the account

1. Run `whoami` from the reviewer session:

   ```sh
   shipd room whoami 412
   ```

2. Read the output. It names the login, the author, and the source:

   ```json
   {"login": "reviewer-b", "author": "mikkel", "source": "GH_TOKEN", "may_approve": true}
   ```

   The `source` value names the first credential `gh` uses, in `gh`'s
   order. On `github.com` the order is `GH_TOKEN`, `GITHUB_TOKEN`,
   `GH_CONFIG_DIR`, then `gh-login`. A CI job that sets only `GITHUB_TOKEN`
   reports `GITHUB_TOKEN`. On a GitHub Enterprise Server host,
   `GH_ENTERPRISE_TOKEN` and `GITHUB_ENTERPRISE_TOKEN` take the place of the
   first two. The source never shows a token.

3. Check the exit code. `whoami` exits `1` with one `Error:` line when `gh`
   cannot read the login. It also exits `1` when the login matches the author,
   ignoring case.

The `/s:room` skill runs `whoami` before every approving review and stops on
the error. `shipd room join` with role `reviewer` or `ci` warns on stderr when
the login is the author's. It still joins.

## Keep the token out of the repository

- Never write a token into a tracked file.
- Never write a token into `.shipd-config.json`.
- Never pass a token as a command-line argument.

## See also

- [Run an agent's turn in a multi-agent PR](pr-room.md) — the room verbs.
- [Multi-agent PR](multi-agent-pr.md) — the model.
- [Semantic review](semantic-review.md) — the gate that posts reviews.
