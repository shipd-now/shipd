## ADDED Requirements

### Requirement: Structural diff subcommand
id: structural-diff

The system SHALL provide `semdiff diff <base> [<head>]` emitting a single
JSON object: resolved endpoint metadata (`base`, `head`, `mode` —
working-tree when head is omitted, merge-base three-dot by default with a
head, two-dot under `--linear`), a per-file list with `path`, `language`,
`kind` (added/deleted/modified), token-level `hunks`, and a `summary` with
file/hunk/kind counts, languages, and a best-effort `signature_changes`
estimate. When reviewing the working tree, untracked files SHALL be
included; whole-file adds/deletes with no hunks SHALL carry a `lines`
count; whitespace-only content edits SHALL be filtered out.

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

### Requirement: Text-engine degradation
id: text-fallback

If the `difft` binary is unavailable, then `semdiff diff` SHALL degrade to
a structural-text engine that parses `git diff` unified output into the
same JSON shape, stamping `engine: "text"` on affected file entries and in
the summary (`engine: "difft"` when syntax-aware), and SHALL NOT exit
non-zero solely because difftastic is missing. If difftastic output fails
to parse for a single file, then only that file SHALL fall back to the
text engine.

#### Scenario: Missing difft degrades instead of blocking
- **WHEN** `semdiff diff main` runs on a machine without `difft`
- **THEN** it exits zero and emits the diff JSON with `engine: "text"`

### Requirement: Cohort grouping subcommand
id: cohort-grouping

The system SHALL provide `semdiff files <base> [<head>]` grouping changed
paths into architectural cohorts using segment-aware rules (contracts,
database, api, frontend, tests; plus shipd-aware groups for content-dir
spec artifacts and plugin skills), falling back to the path's top-level
directory, and emitting JSON with the cohort map and file/cohort counts.

#### Scenario: Segment-aware grouping
- **WHEN** `semdiff files main` runs over changes touching
  `plugins/s/skills/review/SKILL.md` and `.shipd/planned/x/plan.md`
- **THEN** the two paths land in the skills and specs cohorts, not in a
  generic top-level bucket

### Requirement: Reference context subcommand
id: reference-context

The system SHALL provide `semdiff context <symbol> [--path] [--lang]`
returning candidate references as JSON via ripgrep when available, else
`git grep`, and the output SHALL carry an explicit note that matches are
best-effort candidates, never a complete call graph.

#### Scenario: Fallback lookup without ripgrep
- **WHEN** `semdiff context parse_spec` runs where `rg` is absent
- **THEN** matches come from `git grep` with file, line, and text, and the
  best-effort note is present

### Requirement: Planned-change review bridge
id: change-bridge

The system SHALL provide `semdiff change <name>` aggregating a planned am
change's review context as one JSON object: the change status, per-delta
entries (operation, capability, requirement id and text, scenario texts),
task checkbox states with progress counts, the change's lint findings, and
best-effort impact files extracted from `plan.md`. It SHALL resolve the
content directory through the engine's layered configuration and reuse the
engine's parser in-process, and SHALL exit non-zero with a clear message
when the change does not exist under `planned/`.

#### Scenario: Aggregated change context
- **WHEN** `semdiff change my-change` runs against a lint-clean planned
  change with two delta requirements and three tasks, one checked
- **THEN** the JSON lists both requirements with their scenarios and
  reports task progress 1 of 3 with no lint findings

#### Scenario: Unknown change fails clearly
- **WHEN** `semdiff change nope` runs and `planned/nope/` does not exist
- **THEN** it exits non-zero naming the missing change

### Requirement: Dependency doctor with tiered installer
id: doctor-provisioning

The system SHALL provide `semdiff doctor` reporting tool availability —
git required; difft recommended (absence degrades review, never blocks);
rg and gh optional — with actionable hints, exiting non-zero only when a
required tool is missing. Where `--fix` is given, the system SHALL install
difftastic by trying Homebrew, then cargo, then a prebuilt release binary
into the plugin's `bin/` (else `~/.local/bin`); network access SHALL occur
only under `--fix`.

#### Scenario: Doctor reports without installing
- **WHEN** `semdiff doctor` runs without `--fix` on a machine missing difft
- **THEN** difft is reported as recommended-missing with an install hint,
  no network access occurs, and the exit code is zero when git is present

### Requirement: Semantic review skill
id: review-skill

The plugin SHALL provide an `/s:review` skill that reviews local changes
against a base ref (default `main`, or a named base/head pair) by mapping
cohorts foundational-first, reasoning over the semdiff structural diff
rather than raw file dumps, chasing changed signatures through `semdiff
context`, and reporting findings by cohort, each with location, what, why,
a concrete fix, and a severity of high, medium, or low. The rendered
report SHALL carry an effort score (1–5), a findings header reading
`## Findings: ✅ Ship it` when no finding is high or medium and
`## Findings: ❌ Fix required` otherwise, a summary table rating findings
with 🔴/🟠/🟡 severity dots, a collapsible walkthrough, and an explicit
list of what could not be verified. Emoji SHALL appear only at those two
sites; branding is shipd-only, and the skill SHALL NOT modify the repo.

#### Scenario: Blocking verdict matches severities
- **WHEN** a review yields one medium and one low finding
- **THEN** the header reads `## Findings: ❌ Fix required` and the summary
  table rates them 🟠 and 🟡

#### Scenario: Machine mode for the gate
- **WHEN** the skill is invoked with `--json`
- **THEN** it emits only a JSON object — verdict `changes-requested` iff
  any finding is high or medium, else `pass`, with findings, optional
  spec_coverage, and could_not_verify arrays — and no emoji or prose

### Requirement: Spec-aware verification
id: spec-aware-review

Where a planned change is named by the user or exactly one change exists
under `planned/`, the skill SHALL verify the diff against `semdiff change`
output: classify every delta scenario as Met (citing the satisfying hunk),
Unmet, or Can't-tell; report each unmet scenario as a high-severity
spec-coverage finding; flag checked tasks with no supporting change in the
diff; and surface behavioral changes no requirement or task describes as
observations, not blockers.

#### Scenario: Unmet scenario tops the findings
- **WHEN** a delta scenario's behavior is absent from the structural diff
- **THEN** the review reports it as a high-severity spec-coverage finding
  and the verdict is Fix required

### Requirement: Engine test coverage in ci
id: review-test-coverage

The semdiff script SHALL be covered by a unittest suite under
`plugins/s/skills/review/tests/` that builds fixture git repositories in
temporary directories, skips difft-dependent assertions when difftastic is
absent, performs no network access, and is discovered by the `ci`
workflow.

#### Scenario: ci discovers the review suite
- **WHEN** the ci workflow runs on a runner without difftastic
- **THEN** the review tests run via unittest discovery and pass,
  exercising the text engine
