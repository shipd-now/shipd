## MODIFIED Requirements

### Requirement: Doctor GitHub-side gate checks
id: doctor-github-checks
base: f6b6e168c591
Dropped: No GitHub remote skips all three checks

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
`gh api repos/<nwo>/branches/<default>/protection`: when the response lists
required status contexts containing `semantic-review` it SHALL report `ok`;
when the contexts omit `semantic-review` it SHALL `warn` naming the missing
context; when the response is 404 (unprotected) it SHALL `warn` naming the
unprotected default branch; when the response is 403 (no admin) it SHALL fall
back to the branches listing's `protected` boolean, reporting `ok` with a
contexts-unverifiable note when `true` and `warn` when `false`.

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
