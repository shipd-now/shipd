# GitHub merge enforcement without a GitHub App

Findings gathered while planning the merge-rules epic, on what GitHub
repository rulesets can enforce before a pull request merges.

## What rulesets enforce

- **Required approving reviews.** A count of approvals from accounts with
  write access. GitHub never counts the pull request author's own approval.
- **Dismiss stale approvals.** A push that changes the diff dismisses earlier
  approvals.
- **Require approval of the most recent reviewable push.** Someone other than
  the last pusher must approve.
- **Required conversation resolution** and **allowed merge methods.**
- **Required status checks.** Each check belongs to a commit, so a check green
  on an older commit does not satisfy the head. Strict mode additionally
  requires the head branch to include the latest base.
- **Check source pinning.** A required check can name a GitHub App as its
  expected source; a status from anyone else then blocks the merge. A status
  posted with a personal token has no app source, so it cannot be pinned.

## Who counts as an approver

- **A second user account** (a machine account) with write access counts like
  any collaborator.
- **github-actions[bot]** approvals count when the repository allows GitHub
  Actions to create and approve pull requests (an org setting can forbid it).
- **Copilot** reviews do not count toward required approvals by default.

## Sources

- [Available rules for rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
- [Approving a pull request with required reviews](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/approving-a-pull-request-with-required-reviews)
- [GitHub Actions: prevent GitHub Actions from approving pull requests](https://github.blog/changelog/2022-01-13-github-actions-prevent-github-actions-from-approving-pull-requests)
- [GHA bot review is not affecting merge requirements](https://github.com/orgs/community/discussions/181487)
