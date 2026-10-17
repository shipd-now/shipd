## ADDED Requirements

### Requirement: Gate offers the Actions approval setting
id: gate-actions-approval-consent

In addition to the steps `gate-skill-flow` lists, the `/s:gate` consent round
SHALL carry one optional row that runs
`python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/actions_approval.py" allow --repo <nwo>`,
stating in plain words that it lets GitHub Actions create and approve pull
requests so github-actions[bot] can count as a required approver, and that any
workflow in the repository could then approve. The row SHALL be recommended
only when the user wants the CI reviewer to count toward required approvals,
SHALL run only on a consent answer naming it, and a denial (admin right or
organization policy) SHALL be reported with the manual hint (Settings,
Actions, General, Workflow permissions) without blocking the other consented
steps. Before the round the skill SHALL run the same script bare and show the
current state. The closing report SHALL state when the setting is off that the
CI reviewer's approval degrades to a comment.

#### Scenario: The row is optional and named
- **WHEN** the user consents to other steps but not this one
- **THEN** no `allow` call is made and the closing report says the CI reviewer's approval will not count

#### Scenario: Declining runs nothing
- **WHEN** the user declines every step
- **THEN** the script is run bare at most, never with `allow`

#### Scenario: A denied write is a hint, not a stop
- **WHEN** the `allow` call exits non-zero
- **THEN** the skill reports the manual path and continues with the remaining consented steps
