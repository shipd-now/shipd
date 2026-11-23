<!-- doc-type: how-to -->

# Pull requests

Every change ships as one pull request, opened from its `change/<slug>` branch. `/s:pr` writes the
title and the body of that pull request, then creates it or updates it.

The pull request merges once its required checks pass. A ruleset on GitHub holds the merge rules,
and `shipd gate rules` writes that ruleset from your configuration.

## When to use it

`/s:build` and `/s:autopilot` open the pull request themselves, so a built change needs no extra
step. Run the commands on this page by hand in these cases:

- Run `/s:pr` on a pushed branch that has no pull request yet.
- Run `/s:pr` to rewrite the title or the body of an open pull request.
- Run `shipd gate rules` to check or set the rules a pull request must meet before it merges.

## How to run it

### Write the pull request

1. Push the branch first. `/s:pr` never pushes.

   ```bash
   git push -u origin change/<slug>
   ```

2. Run the skill from the branch:

   ```
   /s:pr
   ```

The skill reads the change on a `change/<slug>` branch: the change's idea gives the why, and its
tasks give what changed. On any other branch, it reads the commit log and the diff stat instead.

The skill writes the body in a fixed shape:

- The first line is exactly `## ☕ Pull Request`.
- A why-first paragraph says what a person sees today, and what the change fixes.
- A short list names what changed, one bullet per effect a user can see.

The skill lints the body against the shipd documentation standard and fixes it until the lint
passes. It renders the title from the `pr.title` template. A ticket id
comes from `--ticket`, or from the branch name through `pr.ticket_pattern`.

When the branch has no pull request, the skill creates one. When the branch has one, the skill
updates its title and body and leaves its draft state as it is. It then prints the full URL of the
pull request.

The skill never pushes and never arms auto-merge. The caller does both.

### Merge it

Arm auto-merge after `/s:pr` opens the pull request:

```bash
gh pr merge --auto --squash --delete-branch
```

GitHub then squashes the pull request and deletes its branch once the merge rules pass. The default
rules require two checks, `ci` and `semantic-review`, and zero unresolved review conversations.
They bind once `shipd gate rules apply` writes them. The [review gate](copilot-review.md) posts the
`semantic-review` check.

Under `pr-mode: draft`, the build opens a draft pull request and arms no auto-merge, so a person
merges it.

### Set the merge rules

The `merge` configuration key holds the rules: the approvals and the status checks a pull request
needs before it merges. `shipd gate rules` compares that key with the ruleset on GitHub.

1. Report the rules. This form prints each member of the `merge` configuration beside the live
   ruleset, and changes nothing:

   ```bash
   shipd gate rules
   ```

2. Apply the rules. This form creates or updates the one ruleset named `shipd merge rules`, and
   writes nothing else:

   ```bash
   shipd gate rules apply
   ```

Applying needs admin permission on the repository. A refusal names the missing admin permission.

`/s:gate` offers the apply step in its consent round, beside the preview from bare
`shipd gate rules`. Afterwards, `shipd doctor` reports drift between the configuration and the
ruleset on its `merge-rules` line.

## Reference

The `/s:pr` flags:

| flag | effect |
| --- | --- |
| `--ticket <id>` | Sets the ticket id for the title. |
| `--draft` | Opens the pull request as a draft. |
| `--base <ref>` | Sets the ref the pull request targets. Default: the repository's default branch. |

The `shipd gate rules` forms:

| form | effect |
| --- | --- |
| `shipd gate rules` | Prints the `merge` configuration beside the live ruleset. Changes nothing. |
| `shipd gate rules apply` | Creates or updates the `shipd merge rules` ruleset. |
| `--repo <owner/name>` | Names the repository. Default: the one `gh repo view` resolves from `--root`. |
| `--root <dir>` | Names the repository root. Default: the current directory. |

Related pages:

- [Customising shipd](customise.md) — the `pr`, `pr-mode`, and `merge` keys
- [The semantic review](semantic-review.md) — the review behind the `semantic-review` check
- [Review gate](copilot-review.md) — posts that check on every pull request
- [Give an agent its own GitHub account](agent-identity.md) — the second account a reviewer
  agent approves from
