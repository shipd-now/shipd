## MODIFIED Requirements

### Requirement: Structural diff subcommand
id: structural-diff
base: 2c92201ae339

The system SHALL provide `semdiff diff <base> [<head>]` emitting a single
JSON object: resolved endpoint metadata (`base`, `head`, `mode` —
working-tree when head is omitted, merge-base three-dot by default with a
head, two-dot under `--linear`), a per-file list with `path`, `language`,
`kind` (added/deleted/modified), token-level `hunks`, and a `summary` with
file/hunk/kind counts, languages, and a best-effort `signature_changes`
estimate. When reviewing the working tree, untracked files SHALL be
included; whole-file adds/deletes with no hunks SHALL carry a `lines`
count; whitespace-only content edits SHALL be filtered out. Kind
classification SHALL distinguish a file that is present at an endpoint
with empty content from a file absent at that endpoint: emptying an
existing file classifies `modified`, never `deleted`, and adding content
to an existing empty file classifies `modified`, never `added`.

#### Scenario: Working-tree review against a base
- **WHEN** `semdiff diff main` runs in a repo with one modified tracked
  file and one untracked file
- **THEN** the JSON reports `mode: working-tree` and both paths, with kinds
  `modified` and `added`

#### Scenario: PR-style head comparison
- **WHEN** `semdiff diff main feature` runs
- **THEN** the JSON reports `mode: merge-base` with the resolved
  `merge_base`, and the after-side content comes from the `feature` ref,
  not the checkout

#### Scenario: Empty is not absent
- **WHEN** `semdiff diff HEAD` runs after emptying one committed non-empty
  file and writing content into another committed empty file
- **THEN** both files report kind `modified` — neither `deleted` nor
  `added`

### Requirement: Dependency doctor with tiered installer
id: doctor-provisioning
base: 96cab5963cf2

The system SHALL provide `semdiff doctor` reporting tool availability —
git required; difft recommended (absence degrades review, never blocks);
rg and gh optional — with actionable hints, exiting non-zero only when a
required tool is missing. Where `--fix` is given, the system SHALL install
difftastic by trying Homebrew, then cargo, then a prebuilt release binary
into the plugin's `bin/` (else `~/.local/bin`); network access SHALL occur
only under `--fix`. The release-binary path SHALL extract only an archive
member that is a regular file: a member named `difft` that is a symlink or
any other non-regular type SHALL be refused with a clear error and nothing
extracted.

#### Scenario: Doctor reports without installing
- **WHEN** `semdiff doctor` runs without `--fix` on a machine missing difft
- **THEN** difft is reported as recommended-missing with an install hint,
  no network access occurs, and the exit code is zero when git is present

#### Scenario: A non-regular archive member is refused
- **WHEN** the release-binary installer encounters an archive whose only
  `difft` member is a symlink
- **THEN** nothing is extracted and the failure names the non-regular
  member, while an archive with a regular-file `difft` member extracts it
