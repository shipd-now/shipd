# actions-approval

### Requirement: Actions approval setting reader and setter
id: actions-approval-setting

`skills/build/scripts/actions_approval.py` SHALL read a repository's
workflow approval permission with `gh api repos/<nwo>/actions/permissions/workflow`
and report `can_approve_pull_request_reviews` as `enabled`, `disabled`, or
`unknown` (a failed call or an unparseable answer), through an injectable
`gh` runner `run(args, stdin=None, cwd=None) -> (code, out, err)`. Bare
invocation SHALL be read-only. The `allow` verb SHALL write only when the
setting reads `disabled`, with `gh api -X PUT` of a JSON body on stdin that
sets `can_approve_pull_request_reviews` to true and carries the
`default_workflow_permissions` value it just read unchanged, then re-read and
report the result. It SHALL write nothing when the setting already reads
`enabled` or `unknown`, SHALL exit non-zero on a failed write or re-read that
does not read `enabled` (an organization policy can override the repository),
and SHALL exit 2 on bad usage.

#### Scenario: Reading a disabled setting
- **WHEN** the runner answers `{"default_workflow_permissions":"read","can_approve_pull_request_reviews":false}`
- **THEN** the bare verb prints `actions-approve: disabled` and issues no write

#### Scenario: Allow preserves the default permissions
- **WHEN** `allow` runs against a disabled setting whose default permissions are `read`
- **THEN** exactly one PUT is issued whose stdin body is
  `{"default_workflow_permissions":"read","can_approve_pull_request_reviews":true}`
  and the verb re-reads the setting before reporting

#### Scenario: Allow is a no-op when already enabled
- **WHEN** `allow` runs and the setting reads `enabled`
- **THEN** no PUT is issued and the verb exits 0

#### Scenario: An unreadable setting is never written
- **WHEN** the read fails or returns non-JSON
- **THEN** the verb prints `actions-approve: unknown`, issues no PUT, and `allow` exits non-zero

#### Scenario: A write that does not take is reported
- **WHEN** the PUT succeeds but the re-read still reads `disabled`
- **THEN** the verb names an organization policy as the likely cause and exits non-zero

### Requirement: CI reviewer approval ships tests, docs, and a version bump
id: ci-reviewer-docs-version

The change SHALL cover `actions_approval.py` and the workflow's review event
with offline tests, update `docs/copilot-review.md` and
`docs/copilot-review-reference.md` to describe the CI reviewer's decision
review and the repository setting it needs, and advance the plugin version in
`plugins/s/.claude-plugin/plugin.json` by one patch above the value `main`
carries.

#### Scenario: Offline suites pass
- **WHEN** `python3 -m unittest discover -s plugins/s/skills/build/tests` runs with no network
- **THEN** it reports `OK`

#### Scenario: Version guard passes
- **WHEN** `version_guard.py --base main --head HEAD` runs on the change
- **THEN** it exits `0`
