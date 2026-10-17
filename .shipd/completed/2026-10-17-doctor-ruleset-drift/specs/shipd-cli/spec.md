## MODIFIED Requirements

### Requirement: Doctor GitHub-side gate checks
id: doctor-github-checks
base: 87a74d8dd224

The `doctor` verb SHALL additionally report four GitHub-side checks —
`protection`, `automerge`, `copilot-secret`, and `fast-pass`, in that order
directly after `statusline` — probed read-only through the `gh` CLI, each behind an
injectable runner so the test suite never touches the network, and each
reporting `warn` at worst. If `gh` is absent or unauthenticated, or the
working directory resolves no GitHub repository (via
`gh repo view --json nameWithOwner`), or any probe fails for any other
reason (offline, an API error, a missing payload field), then the affected
check SHALL report `ok` with a note naming why it was skipped or could not be
verified — the preflight SHALL never fail, and never warn falsely, from an
unreachable or unreadable GitHub API. The verb SHALL resolve the repository
payload (`gh api repos/<nwo>`: default branch, `allow_auto_merge`,
`permissions.admin`) at most once and reuse it across the checks, and every
`warn` detail SHALL state when the token lacks admin permission, so the
consuming skill knows the fix is unavailable. The verb SHALL continue to
mutate nothing.

The `protection` check SHALL probe
`gh api repos/<nwo>/branches/<default>/protection` and, when that probe does
not already show `semantic-review` required, also the effective branch rules
`gh api repos/<nwo>/rules/branches/<default>` (which includes organisation
rulesets and needs no admin permission), and SHALL judge the union of the
required status contexts from both: when the union contains `semantic-review`
it SHALL report `ok` naming the source (classic protection or a ruleset);
when a ruleset protects the branch (the rules list is non-empty) or classic
protection does, and the union omits `semantic-review`, it SHALL `warn`
naming the missing context and, for a ruleset, saying so; only when neither
source protects the branch (classic 404 and an empty rules list) SHALL it
`warn` naming the unprotected default branch. When the classic probe is 403
(no admin) the check SHALL consult the rules list before the branches
listing's `protected` boolean, and a rules-list probe that fails SHALL leave
the classic outcome standing, never a false alarm.

The `automerge` check SHALL report `ok` when the repository payload's
`allow_auto_merge` is `true`; when it is `false` and the resolved `pr-mode`
is `draft` it SHALL report `ok` with a draft-mode note; when it is `false`
otherwise it SHALL `warn`; when the field is absent it SHALL report `ok`
with an unverifiable note.

Where `.github/workflows/copilot-review-gate.yml` exists at the
working-directory root, the `copilot-secret` check SHALL probe the
repository's Actions secrets: it SHALL report `ok` naming the CLI reviewer
mode when `COPILOT_GITHUB_TOKEN` is listed, SHALL `warn` naming the
fail-open poll fallback when the listing succeeds without it, and SHALL
report `ok` with an unverifiable note when the listing is denied. Where that
workflow file does not exist, the check SHALL report `ok` with a skipped
note.

The `fast-pass` check SHALL probe the repository Actions variable
`SHIPD_FAST_PASS` read-only through the same injectable runner: it SHALL report
`ok` naming unattended merging as enabled where the variable reads exactly
`true`, `ok` naming it off where the variable is absent or reads anything else,
and `ok` with an unverifiable note where the read is denied. The check SHALL
never `warn`: the fast-pass being off is the safe default and the fast-pass
being on is a consented setting, so neither state is a problem to report.

#### Scenario: No GitHub remote skips every GitHub-side check
- **WHEN** `shipd doctor` runs in a repository that resolves no GitHub
  repository through `gh repo view`
- **THEN** `protection`, `automerge`, `copilot-secret`, and `fast-pass` each
  report `ok` with a note naming why they were skipped, and the exit code is
  unaffected

#### Scenario: Unprotected default branch warns
- **WHEN** `shipd doctor` runs where the protection probe returns 404 for the
  default branch
- **THEN** a `warn protection — ` line names the unprotected default branch

#### Scenario: A ruleset-protected branch is not called unprotected
- **WHEN** `shipd doctor` runs where the classic protection probe returns 404
  and the effective branch rules list a `required_status_checks` rule whose
  contexts include `semantic-review`
- **THEN** the `protection` line begins `ok` and names the ruleset as the
  source

#### Scenario: A ruleset without the semantic-review context warns
- **WHEN** the classic probe returns 404 and the effective rules list is
  non-empty but requires no `semantic-review` context
- **THEN** a `warn protection — ` line names the missing context and the
  ruleset, and does not say the branch is unprotected

#### Scenario: Protection missing the semantic-review context warns
- **WHEN** `shipd doctor` runs where the protection probe returns required
  status contexts without `semantic-review`
- **THEN** a `warn protection — ` line names the missing `semantic-review`
  context

#### Scenario: Non-admin token falls back to the protected boolean
- **WHEN** `shipd doctor` runs where the protection probe returns 403 and the
  branches listing reports the default branch `protected: true`
- **THEN** the `protection` line begins `ok` and notes the required contexts
  could not be verified without admin

#### Scenario: Draft pr-mode waives the automerge warning
- **WHEN** `shipd doctor` runs where `allow_auto_merge` is `false` and the
  layered configuration declares `pr-mode: draft`
- **THEN** the `automerge` line begins `ok` and names the draft mode

#### Scenario: Disabled auto-merge warns under auto pr-mode
- **WHEN** `shipd doctor` runs where `allow_auto_merge` is `false` and no
  layer declares a `pr-mode`
- **THEN** a `warn automerge — ` line is printed and the exit code is `0`

#### Scenario: Installed gate without the secret warns fail-open
- **WHEN** `shipd doctor` runs where
  `.github/workflows/copilot-review-gate.yml` exists and the secrets listing
  succeeds without `COPILOT_GITHUB_TOKEN`
- **THEN** a `warn copilot-secret — ` line names the fail-open poll fallback

#### Scenario: Absent gate workflow skips the secret check
- **WHEN** `shipd doctor` runs in a repository with no
  `.github/workflows/copilot-review-gate.yml`
- **THEN** the `copilot-secret` line begins `ok` and notes the check was
  skipped

#### Scenario: An enabled fast-pass is reported
- **WHEN** `shipd doctor` runs where `SHIPD_FAST_PASS` reads `true`
- **THEN** the `fast-pass` line begins `ok` and names unattended merging as
  enabled

#### Scenario: An absent variable reports the fast-pass off
- **WHEN** `shipd doctor` runs where `SHIPD_FAST_PASS` is unset
- **THEN** the `fast-pass` line begins `ok` and names the fast-pass as off

#### Scenario: A denied variable read never warns
- **WHEN** `shipd doctor` runs where the variable read is denied
- **THEN** the `fast-pass` line begins `ok` with an unverifiable note and the
  exit code is `0`

## ADDED Requirements

### Requirement: Doctor merge-rules drift check
id: doctor-merge-rules-check

The `doctor` verb SHALL report a `merge-rules` check directly after
`fast-pass`, read-only through the injectable `gh` runner. It SHALL resolve the
`merge` configuration with `resolve_merge`, find the repository's
`shipd merge rules` ruleset with `merge_rules.find_owned`, and compare them
with `merge_rules.diff` (all from `merge-rules-config`). When nothing differs
it SHALL report `ok`. When members differ, or no such ruleset exists, it SHALL
`warn` with one line listing each differing member as `member: live X, wanted
Y` joined by `; `, ending with a pointer to `shipd gate rules` (the
member-per-line report) and `shipd gate rules apply` through `/s:gate`. When the
`merge` configuration is invalid it SHALL `warn` naming the error. When GitHub
is unreadable, the ruleset lookup raises, or the context is skipped, it SHALL
report `ok` with a skipped or unverifiable note. The check SHALL write nothing.

#### Scenario: Matching ruleset is ok
- **WHEN** the live `shipd merge rules` ruleset matches the resolved config
- **THEN** the `merge-rules` line begins `ok`

#### Scenario: Drift is warned member by member
- **WHEN** the live ruleset requires 0 approvals and config wants 2
- **THEN** a `warn merge-rules — ` line contains `approvals: live 0, wanted 2`
  and names `shipd gate rules`, and the exit code is `0`

#### Scenario: Missing ruleset warns
- **WHEN** no ruleset named `shipd merge rules` exists
- **THEN** a `warn merge-rules — ` line names `shipd gate rules apply`

#### Scenario: Unreadable GitHub never warns
- **WHEN** the ruleset lookup fails or raises
- **THEN** the line begins `ok` with a note that it could not be verified

### Requirement: Doctor Actions-approval check
id: doctor-actions-approve-check

The `doctor` verb SHALL report an `actions-approve` check directly after
`merge-rules`. Where `.github/workflows/copilot-review-gate.yml` exists at the
root it SHALL read `gh api repos/<nwo>/actions/permissions/workflow` and report
`ok` when `can_approve_pull_request_reviews` is `true`, and `warn` when it is
`false`, saying the CI reviewer cannot approve until an admin enables the
setting through `/s:gate`. Where the workflow is absent, the context is
skipped, or the read is denied, it SHALL report `ok` with a skipped or
unverifiable note. The check SHALL write nothing.

#### Scenario: Setting off warns where the gate is installed
- **WHEN** the gate workflow exists and the setting reads `false`
- **THEN** a `warn actions-approve — ` line is printed

#### Scenario: Setting on is ok
- **WHEN** the gate workflow exists and the setting reads `true`
- **THEN** the line begins `ok`

#### Scenario: No gate workflow skips
- **WHEN** the gate workflow is absent
- **THEN** the line begins `ok` and notes it was skipped

### Requirement: New GitHub checks are report-only under fix
id: doctor-new-checks-report-only

Under `doctor --fix` the `merge-rules` and `actions-approve` checks SHALL stay
report-only, naming `/s:gate` (`shipd gate rules apply`) as the consent-gated
remedy, and a `protection` finding sourced from a ruleset SHALL likewise run no
remedy.

#### Scenario: Fix performs no GitHub mutation for the new checks
- **WHEN** `shipd doctor --fix` meets a `warn merge-rules` line
- **THEN** no `gh` mutation runs and the line carries a `/s:gate` fix hint
