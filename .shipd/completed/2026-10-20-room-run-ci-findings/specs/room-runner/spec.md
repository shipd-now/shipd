## ADDED Requirements

### Requirement: An author run acts on the CI reviewer's fix-required review
id: room-run-ci-findings

While the role is `author` and `--ci-reviewer` (default `github-actions[bot]`) is non-empty, the run SHALL watch in slices of at most four `--interval` periods. After the kick-off and after every slice that surfaces no task, it SHALL read the pull request's reviews. A review matches when its author login equals `--ci-reviewer` ignoring case, its commit is the current head, and its body carries `<!-- shipd-verdict: fix-required -->`. For the newest matching review not yet handled in this run, the run SHALL mark every matching review handled and spend one resumed author turn whose prompt names the review and tells the author to fix and push, or reply with the reason. That turn SHALL count toward `--max-turns` and SHALL open re-reviews on a moved head exactly as a task turn does. A failed reviews read SHALL warn once on stderr and run no turn. A reviewer or `ci` run, or an empty `--ci-reviewer`, SHALL read no reviews and keep a single watch over the remaining budget.

#### Scenario: A fix-required review of the head starts one turn
- **WHEN** an author run sees a `github-actions[bot]` review of the head carrying the fix-required marker
- **THEN** it runs one turn whose prompt names that review, and a second check runs no further turn for it

#### Scenario: Other reviews start nothing
- **WHEN** the only reviews are a ship-it review, a fix-required review of an older head, or one by another login
- **THEN** the run spends no turn on them

#### Scenario: A pushed fix requests a re-review
- **WHEN** the CI turn moves the head and the run was started with `--request-review reviewer-b`
- **THEN** a re-review task is opened to `reviewer-b` at the new head

#### Scenario: A reviewer run never reads reviews
- **WHEN** a reviewer run waits for tasks
- **THEN** it makes no reviews read
