<!-- doc-type: how-to -->

# Episode 8: CI and Copilot review

## Introduction

A merge needs a check that a person cannot skip, and a spec library needs a check that it stays valid. This episode shows two gates. The lint action checks the spec library in CI. The Copilot review gate posts the `semantic-review` status that blocks a merge. The episode is for maintainers who protect a repository's main branch.

## At a glance

| Item | Detail |
|---|---|
| Roadmap group | Verification and governance |
| Runtime | 5 minutes |
| Prerequisites | [Episode 2](02-worktrees-and-small-prs.md); a GitHub repository with a paid Copilot plan |
| Commands shown | `/s:review`, `shipd copilot add`, `gh secret set`, `shipd doctor` |

## Script

### 0:00–0:45 Two gates

**On screen:** A slide shows a pull request with two required checks, `ci` and `semantic-review`. A red cross marks each missing check.

**Narration:** A gate is a check that blocks a merge until it passes. Shipd uses two. The `ci` gate validates the spec library. The `semantic-review` gate reviews the diff.

### 0:45–1:45 The lint action

**On screen:** A workflow file shows a checkout step, then a `uses: shipd-now/shipd@<ref>` step. The `path` input shows its default of `.`.

**Narration:** The repository carries a composite GitHub Action. It lints the master library, then each planned change. A lint finding fails the action, and a clean repository passes. The action needs only `python3` on the runner. Pin the action to a ref.

### 1:45–2:45 The semantic review

**On screen:** The terminal runs `/s:review`. The report groups findings by cohort and marks each as high, medium, or low.

**Narration:** The semantic review compares two refs through a structural diff. It chases changed signatures to their call sites. High and medium findings block the merge. Low findings do not. An exposed secret always rates high.

### 2:45–4:00 Install the Copilot gate

**On screen:** The terminal runs `shipd copilot add`, which lists four written files. Then `git commit` and `git push` publish them.

**Narration:** The `shipd copilot add` command installs the review as a Copilot agent skill, plus two workflows. Commit and push the files. Copilot reads them from the pull request's head branch, so files that stay on disk are invisible. In a Claude Code session, `/s:gate` runs this whole guide for you.

### 4:00–5:00 The token and the check

**On screen:** The terminal runs `gh secret set COPILOT_GITHUB_TOKEN`, then `shipd doctor`. The last three lines show `protection`, `automerge`, and `copilot-secret`.

**Narration:** Give the reviewer token one permission, Copilot Requests, and no repository access. Store it as a repository secret. An expired token never greens a check, because the status stays pending. Run `shipd doctor` to verify the three GitHub settings.

## Takeaways

- The lint action fails CI when the spec library or a planned change is invalid.
- The `semantic-review` gate blocks a merge on high and medium findings.
- The reviewer token carries Copilot Requests and nothing else.

## Next

[Episode 9](09-management-plane.md) shows the commercial management plane that reads this delivery state.

## Sources

- [Install the Copilot review gate](../../copilot-review.md)
- [The semantic review](../../semantic-review.md)
- [Copilot review reference](../../copilot-review-reference.md)
- [The ci-action spec](../../../.shipd/verified/ci-action/spec.md)
