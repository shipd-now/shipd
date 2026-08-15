## ADDED Requirements

### Requirement: Gated default branch on shipd
id: gate-branch-protection

The `shipd-now/shipd` repository's default branch SHALL be protected so that a
pull request is required before merging, `ci` and `semantic-review` are both
required status check contexts, conversation resolution is required, and the
protection is enforced for administrators. The `semantic-review` context and the
conversation-resolution requirement SHALL be installed by shipd's own ported
gate verb at `plugins/s/skills/review/scripts/review_gate.py`, layered onto a
protection that already requires `ci`.

#### Scenario: Both checks and conversation resolution are required
- **WHEN** the default branch's protection is read from the GitHub API
- **THEN** the required status check contexts contain `ci` and
  `semantic-review`, conversation resolution is required, and administrators are
  not exempt

#### Scenario: The gate verb reports the installed contexts
- **WHEN** `review_gate.py protect` is run from the shipd checkout against the
  protected default branch
- **THEN** it reports `semantic-review` among the resulting contexts and
  conversation resolution as required, leaving the protection unchanged

#### Scenario: A direct push to the default branch is refused
- **WHEN** a commit that is not on the default branch is pushed straight to it
- **THEN** the remote rejects the push

### Requirement: Shipd merges are squash-only and auto-mergeable
id: gate-merge-settings

The `shipd-now/shipd` repository SHALL permit squash merges only — merge commits
and rebase merges disabled — with auto-merge enabled and the head branch deleted
on merge, so that every pull request landing on the default branch produces a
single commit whose subject is the pull request title and can be armed with
`--auto --squash --delete-branch`.

#### Scenario: Only the squash path is permitted
- **WHEN** the repository object is read from the GitHub API
- **THEN** `allow_squash_merge`, `allow_auto_merge`, and
  `delete_branch_on_merge` are all true, and `allow_merge_commit` and
  `allow_rebase_merge` are both false

### Requirement: The port stack is on shipd's default branch
id: gate-stack-landed

Each of the six port member branches — `shipd-port-tool`, `shipd-engine-port`,
`shipd-library-port`, `shipd-identity`, `shipd-brand`, and `shipd-evals-port` —
SHALL be merged into shipd's default branch through its own pull request, with
the branch's `ci` workflow concluding successfully on the resulting default
branch, and no member branch left unmerged.

Because these six landed as merge commits before this repository's merge
settings were restricted, the default branch's subject lines do not resolve
uniformly: four of the six slugs — `shipd-port-tool`, `shipd-engine-port`,
`shipd-library-port`, and `shipd-evals-port` — have no commit whose subject
begins with the slug and a colon; `shipd-brand` has two; and `shipd-identity`
has exactly one and therefore still resolves. `metrics.py`'s `git_change_times`
can resolve a merge commit for `shipd-identity` alone, and not for the other
five. This SHALL be recorded as an accepted consequence: the history is not
rewritten to repair it, and `gate-merge-settings` prevents its recurrence.

#### Scenario: Every member is merged
- **WHEN** the repository's pull requests are read after the stack has landed
- **THEN** each of the six member branches has a pull request in a merged state
  and none of the six branches remains on the remote

#### Scenario: The default branch carries the whole port
- **WHEN** the default branch is checked out after the six merges
- **THEN** `plugins/s/`, `.shipd/`, `tools/port.py`, `evals/`, and
  `.github/workflows/ci.yml` are all present and the `ci` workflow run for that
  push succeeds

#### Scenario: The metrics gap is recorded rather than repaired
- **WHEN** the default branch's history is searched for subjects beginning with
  each member slug and a colon
- **THEN** the counts are zero for `shipd-port-tool`, `shipd-engine-port`,
  `shipd-library-port` and `shipd-evals-port`, one for `shipd-identity`, and two
  for `shipd-brand`, and the history contains no rewritten or force-updated
  member commit

### Requirement: The exercise change transited the gate
id: gate-exercise-transit

The exercise change's pull request SHALL have reached a merged state through the
complete gate with no protection rule bypassed: `ci` passing, a
`semantic-review` commit status of `success` posted by shipd's own gate poster
on the pull request's head commit, and every gate-authored finding thread
dispositioned so no unresolved thread blocked the merge.

#### Scenario: The gate status is posted by shipd's own poster
- **WHEN** the exercise pull request's `semantic-review` commit status is read
- **THEN** its state is `success`, and its target links to the summary comment
  written by `plugins/s/skills/review/scripts/review_gate.py post`

#### Scenario: The merge satisfied both required checks
- **WHEN** the exercise pull request is read after merging
- **THEN** it is in a merged state, its head branch is absent from the remote,
  and the combined status on its head commit is `success` with administrators
  not exempt from the protection

### Requirement: The PR-authoring path is recorded, not rediscovered
id: gate-authoring-path-recorded

The mechanism a session uses to perform GitHub API writes against
`shipd-now/shipd` SHALL be recorded as the answer to the workspace queue entry
`q-shipd-pr-authoring`, naming the mechanism and the scope it requires. No
credential value SHALL be written into a tracked file of either repository or
into any spec artifact.

#### Scenario: The queue entry carries the chosen mechanism
- **WHEN** the workspace queue is read after the gate work has run
- **THEN** the `q-shipd-pr-authoring` entry's answer names the mechanism used
  and the scope it required, and is no longer pending

#### Scenario: No credential value is checked in
- **WHEN** both repositories' tracked files and this change's artifacts are
  searched for the credential's value
- **THEN** no match is found
