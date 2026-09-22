## MODIFIED Requirements

### Requirement: Required difftastic with per-file parse retry
id: text-fallback
base: 1b74073378cf
Dropped: Missing difft degrades instead of blocking

If the `difft` binary is unavailable, then `semdiff diff` SHALL exit
non-zero with a message naming the install remedy and SHALL emit no diff
JSON, rather than degrading to the text engine. A review whose engine
varies silently produces a verdict nobody can reproduce or audit, and the
gate never reads the `engine` field that would have disclosed it. If
difftastic output fails to parse for a single file, then only that file
SHALL fall back to the text engine, stamping `engine: "text"` on that file
entry and on the summary, so a single unparseable file still degrades
rather than failing the run.

#### Scenario: Missing difft fails the diff
- **WHEN** `semdiff diff main` runs on a machine without `difft`
- **THEN** it exits non-zero, emits no diff JSON, and its message names how
  to install difftastic

#### Scenario: A single unparseable file still falls back
- **GIVEN** difftastic is installed but produces output that cannot be
  parsed for one file of several
- **WHEN** `semdiff diff main` runs
- **THEN** it exits zero, that file's entry carries `engine: "text"`, and
  the remaining files stay syntax-aware

### Requirement: Dependency doctor with tiered installer
id: doctor-provisioning
base: 4d69f16f6b4d

The system SHALL provide `semdiff doctor` reporting tool availability —
git and difft required; rg and gh optional — with actionable hints,
exiting non-zero only when a required tool is missing. Where `--fix` is
given, the system SHALL install difftastic by trying Homebrew, then cargo,
then a prebuilt release binary into the plugin's `bin/` (else
`~/.local/bin`); network access SHALL occur only under `--fix`. The
release-binary path SHALL request a pinned release version rather than the
unversioned `releases/latest/download/` asset name, which difftastic
stopped publishing after 0.65.0 and which therefore 404s. The
release-binary path SHALL extract only an archive member that is a regular
file: a member named `difft` that is a symlink or any other non-regular
type SHALL be refused with a clear error and nothing extracted.

#### Scenario: Doctor reports without installing
- **WHEN** `semdiff doctor` runs without `--fix` on a machine missing difft
- **THEN** difft is reported as required-missing with an install hint, no
  network access occurs, and the exit code is non-zero

#### Scenario: A non-regular archive member is refused
- **WHEN** the release-binary installer encounters an archive whose only
  `difft` member is a symlink
- **THEN** nothing is extracted and the failure names the non-regular
  member, while an archive with a regular-file `difft` member extracts it

#### Scenario: The installer requests a pinned version
- **WHEN** the release-binary installer's download URL is inspected
- **THEN** it names a pinned release version rather than
  `releases/latest/download/`

### Requirement: Engine test coverage in ci
id: review-test-coverage
base: 91c08c61b062
Dropped: ci discovers the review suite

The semdiff script SHALL be covered by a unittest suite under
`plugins/s/skills/review/tests/` that builds fixture git repositories in
temporary directories, performs no network access, and is discovered by the
`ci` workflow. The `ci` workflow SHALL install difftastic before running
that suite, so the difft-gated assertions execute in the gating pipeline
rather than being skipped there. The suite SHALL cover the text engine
through the per-file parse-failure retry, which stays reachable, so the
fallback path ships tested even though no review may run wholly on it.

#### Scenario: ci installs difftastic and runs every assertion
- **WHEN** the ci workflow runs the review suite
- **THEN** difftastic is installed first and no test is skipped for its
  absence

#### Scenario: The text engine keeps its coverage
- **WHEN** the review suite runs
- **THEN** at least one test exercises the per-file parse-failure retry and
  asserts the `engine: "text"` stamp it produces

### Requirement: Review-start difftastic auto-fix
id: review-difft-autofix
base: 2f2f67e45837
Dropped: Failed auto-install informs and degrades loudly

When the `/s:review` skill begins a review and `difft` is not on PATH, the
skill SHALL run the tiered installer (`semdiff doctor --fix`) once before
any analysis and re-probe for `difft` afterwards — reaching the network
solely through `--fix`, preserving the installer's network invariant. If
`difft` is still missing after that attempt, then the skill SHALL stop
without reviewing, reporting prominently that difftastic is required, how
to install it manually, and that no verdict was produced. It SHALL NOT
complete the review on the text engine: a review the engine could not
judge syntax-aware is one nobody can reproduce, and reporting it as a
review is worse than reporting nothing. The installer is attempted at most
once per review.

#### Scenario: Successful auto-install restores the syntax-aware engine
- **WHEN** a review starts with `difft` absent and the tiered installer
  succeeds
- **THEN** the review proceeds on the syntax-aware engine with no
  degradation notice

#### Scenario: Failed auto-install stops the review
- **WHEN** a review starts with `difft` absent and the tiered installer
  leaves it missing
- **THEN** the skill stops without analysing, reports that difftastic is
  required with a manual install hint, and produces no verdict

#### Scenario: Present difft skips the installer
- **WHEN** a review starts with `difft` already on PATH
- **THEN** the installer is not invoked and the review proceeds directly

## ADDED Requirements

### Requirement: Documentation states difftastic as required
id: difft-required-docs

The repository's documentation SHALL describe difftastic as required for a
semantic review, and SHALL carry no claim that a review degrades, falls back
to the text engine, or completes without it. `docs/semantic-review.md`'s
missing-tool section SHALL say the review stops without `difft`, and
`docs/copilot-review-reference.md` SHALL NOT list `difft` among optional
tools. Each page SHALL stay within its own doc-type line cap and SHALL read
as a statement of current behaviour, naming no change, no previous
behaviour, and no migration.

#### Scenario: The concept guide says the review stops
- **WHEN** `docs/semantic-review.md`'s missing-tool section is read
- **THEN** it states that a review without `difft` stops, and makes no claim
  that it degrades or falls back

#### Scenario: The reference no longer calls difftastic optional
- **WHEN** `docs/copilot-review-reference.md` is read
- **THEN** `difft` is not described as optional and no text-engine fallback
  is offered for its absence

#### Scenario: The pages stay within their caps
- **WHEN** the documentation lint runs over `docs/semantic-review.md` and
  `docs/copilot-review-reference.md`
- **THEN** it reports no finding
