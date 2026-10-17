# Team merge test evidence

Run of `tools/team_merge_test.py` against mikkel-bergmann/unkannybanny.

- Result: **pass**
- Pull request: https://github.com/mikkel-bergmann/unkannybanny/pull/21
- Started: 2026-10-17T09:47:29Z
- Finished: 2026-10-17T09:57:00Z

## Server facts

| Id | Claim | Observed | Ok | At |
|---|---|---|---|---|
| a-gate-ready | ci and semantic-review are green and the bot approved the head | head=2f0625c052f88d8bd0088575e1b1c2e1402181b4 | yes | 2026-10-17T09:48:40Z |
| a-one-approval-blocks | one approval (the bot) cannot merge: PUT merge is refused and the state is BLOCKED | PUT merge -> HTTP/2.0 405 Method Not Allowed; mergeStateStatus=BLOCKED; approvals=['github-actions[bot]'] | yes | 2026-10-17T09:48:43Z |
| c-author-approval-refused | the author's own approval is refused by GitHub | exit 1: failed to create review: GraphQL: Review Can not approve your own pull request (addPullRequestReview) | yes | 2026-10-17T09:48:45Z |
| c-whoami-author-exit-1 | `shipd room whoami` as the author exits 1 | exit 1: Error: acting as @mikkel-bergmann, who authored mikkel-bergmann/unkannybanny#21; an author cannot approve their own pull request | yes | 2026-10-17T09:48:46Z |
| c-whoami-reviewer-may-approve | `shipd room whoami` as the reviewer exits 0 with may_approve true | exit 0: login=shipd-now may_approve=True | yes | 2026-10-17T09:48:48Z |
| a-two-approvals-clean | two non-author approvals on the head make the state CLEAN with no merge | approvals=['github-actions[bot]', 'shipd-now']; mergeStateStatus=CLEAN; state=OPEN | yes | 2026-10-17T09:48:50Z |
| b-empty-push-keeps-approvals | an empty push leaves the approvals standing (observed on GitHub; the dismissal proof pushes a real change) | review 5557270430 by shipd-now reads not DISMISSED; head 2f0625c052f88d8bd0088575e1b1c2e1402181b4 -> 1f4d8a0a0626551bf77b959f61ee9d500235d800 | yes | 2026-10-17T09:54:08Z |
| b-push-dismisses | a push dismisses the reviewer's approval | review 5557270430 by shipd-now reads DISMISSED; head 1f4d8a0a0626551bf77b959f61ee9d500235d800 -> 9bb6e8780cc6aa1397f5bb8de4c2c0cbf4005bcd | yes | 2026-10-17T09:55:51Z |
| b-probe-after-push | the merge call is refused after the push while checks run | PUT merge -> HTTP/2.0 405 Method Not Allowed | yes | 2026-10-17T09:55:53Z |
| b-only-bot-reapproves | with checks green only the bot re-approved; merge is still refused | head=9bb6e8780cc6aa1397f5bb8de4c2c0cbf4005bcd approvals=['github-actions[bot]']; PUT merge -> HTTP/2.0 405 Method Not Allowed | yes | 2026-10-17T09:56:29Z |
| d-threads-resolved | no unresolved review threads on the head | head=9bb6e8780cc6aa1397f5bb8de4c2c0cbf4005bcd unresolved_threads=0 | yes | 2026-10-17T09:56:30Z |
| d-auto-merge-armed-open | auto-merge is armed last and the pull request stays OPEN on one approval | state=OPEN autoMergeRequest=set approvals=['github-actions[bot]'] | yes | 2026-10-17T09:56:33Z |
| d-merged | the pull request reaches MERGED with no manual merge call | state=MERGED | yes | 2026-10-17T09:56:51Z |
| d-two-nonauthor-approvals | two APPROVED reviews on the merged head come from non-author logins | head=9bb6e8780cc6aa1397f5bb8de4c2c0cbf4005bcd approvals=['github-actions[bot]', 'shipd-now'] author=mikkel-bergmann | yes | 2026-10-17T09:56:52Z |
| e-doctor-no-drift | `shipd doctor` reports ok for protection, merge-rules, and actions-approve | ok protection — `main` requires the `semantic-review` status context through a ruleset; ok merge-rules — the `shipd merge rules` ruleset on mikkel-bergmann/unkannybanny matches the `merge` configuration; ok actions-approve — Actions may approve pull requests on mikkel-bergmann/unkannybanny | yes | 2026-10-17T09:56:59Z |
| e-rules-no-differs | bare `shipd gate rules` shows no `differs` line | exit 0; 0 differs line(s) | yes | 2026-10-17T09:57:00Z |
