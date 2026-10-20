## MODIFIED Requirements

### Requirement: Any push to the head requests a re-review
id: room-run-rereview
base: 6cb5338aa7a3

While the role is `author`, the run SHALL remember the last head it read, starting from a `headRefOid` read made after the kick-off. After every watch slice that surfaces no task, and after every turn that returns ok, the run SHALL read the head again. When that read succeeds, the remembered head is non-empty, and the two differ, the run SHALL open one re-review task, shaped as the kick-off task with `head` the new SHA and text naming it, to each target lacking one for that head, whoever moved the head. It SHALL then remember the new head. The targets are the `--request-review` agents plus every agent whose card role is `reviewer` and who opened a task first addressed to this agent, excluding this agent. A target lacks one when no task exists whose opener is this agent, whose first message is addressed to the target, and whose first message's `head` equals the new SHA. If a head read fails, then the run SHALL warn once on stderr, open no re-review for that read, keep the remembered head, and continue. A reviewer or `ci` run SHALL open no re-review.

#### Scenario: A fix push opens one re-review to the reviewer who filed it
- **WHEN** an author run's fake runner answers a finding task opened by `reviewer-b` (card role `reviewer`) and moves the fake head from `aaa1111` to `bbb2222`
- **THEN** one task is opened to `reviewer-b` with skill `review-finding` and metadata `head` `bbb2222`

#### Scenario: A push by someone else between slices opens one re-review
- **WHEN** an author run started with `--request-review reviewer-b` sees the fake head move from `aaa1111` to `bbb2222` during a watch slice, with no turn run
- **THEN** exactly one task is opened to `reviewer-b` at `head` `bbb2222`, beyond the kick-off task

#### Scenario: The author's own push is requested once
- **WHEN** an author turn moves the head to `bbb2222` and the run then watches more slices
- **THEN** exactly one re-review task to each target exists at `head` `bbb2222`

#### Scenario: The re-review is idempotent per head
- **WHEN** a task opened by `author-a` to `reviewer-b` with `head` `bbb2222` already exists when the head moves to `bbb2222`
- **THEN** no task is opened

#### Scenario: A turn that pushes nothing requests nothing
- **WHEN** an author turn leaves the head at `aaa1111`
- **THEN** no task is opened

#### Scenario: A reviewer run never requests a re-review
- **WHEN** a reviewer run's head moves during a turn or between slices
- **THEN** no task is opened by the run

### Requirement: An author run acts on the CI reviewer's fix-required review
id: room-run-ci-findings
base: dc11bdabd1dc

While the role is `author`, the run SHALL watch in slices of at most four `--interval` periods, and a slice that surfaces no task SHALL not end the run while budget remains. While `--ci-reviewer` (default `github-actions[bot]`) is also non-empty, after the kick-off and after every slice that surfaces no task, the run SHALL read the pull request's reviews. A review matches when its author login equals `--ci-reviewer` ignoring case, its commit is the current head, and its body carries `<!-- shipd-verdict: fix-required -->`. For the newest matching review not yet handled in this run, the run SHALL mark every matching review handled and spend one resumed author turn whose prompt names the review and tells the author to fix and push, or reply with the reason. That turn SHALL count toward `--max-turns` and SHALL open re-reviews on a moved head exactly as a task turn does. A failed reviews read SHALL warn once on stderr and run no turn. A reviewer or `ci` run SHALL read no reviews and keep a single watch over the remaining budget. An author run with an empty `--ci-reviewer` SHALL read no reviews and still watch in slices.

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

#### Scenario: An empty CI reviewer still slices
- **WHEN** an author run with `--ci-reviewer ""`, `--interval 5`, and `--budget 100` waits with no task
- **THEN** every watch timeout is at most `20`, more than one watch runs, and no reviews read is made
