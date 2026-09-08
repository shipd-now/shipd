## MODIFIED Requirements

### Requirement: Epic amend check verb
id: epic-amend-check-verb
base: 5fc947f36cbf

The status CLI SHALL provide `epic-amend-check <slug> [--base <ref>]`
comparing the invocation root's resolved `epics/<slug>/epic.md` — which
under a declared `store_root` lives in an external store's repository —
against its content at the merge-base of `HEAD` and the base ref (default
`main`), read through git (`merge-base`, then `show <sha>:<relpath>`),
without writing anything. The verb SHALL anchor every git invocation on the
directory holding the epic file, never on the invocation root, so the base
version is always read from the repository actually tracking the epic. The
verb SHALL treat the bodies of `## Decisions`, `## References`,
`## Research`, and `## Video` as amendable, and everything else as
protected: the pre-section header block (title and metadata lines),
`## Introduction` (subsections included), `## Design`, `## Changes`,
`## Token usage breakdown`, and any unrecognized level-2 section. When a
protected region's content differs between the two versions — including a
protected section added or removed — the verb SHALL print one
`protected-section <name>` finding line per changed region (`header` for the
pre-section block) followed by a summary line, and SHALL exit 4; when only
amendable bodies changed, or nothing changed, it SHALL report clean and exit
0. If the epic file is missing from the working tree, absent at the
merge-base, the base ref is unresolvable, or the epic's directory is not
inside a git work tree, then the verb SHALL exit non-zero with an error
naming the cause, distinct from the findings exit.

#### Scenario: Decisions-only amendment passes
- **GIVEN** a branch whose only epic edit adds a stamped bullet to
  `## Decisions` and a link entry to `## References`
- **WHEN** `epic-amend-check <slug>` runs
- **THEN** no finding line prints, the summary reports clean, and the exit
  code is 0

#### Scenario: Protected-section edit is a finding
- **GIVEN** a branch that edits the epic's `## Introduction` and a
  `## Changes` stub row
- **WHEN** `epic-amend-check <slug>` runs
- **THEN** `protected-section ## Introduction` and
  `protected-section ## Changes` finding lines print and the exit code is 4

#### Scenario: Header metadata edit is a finding
- **GIVEN** a branch that changes the epic's `Status:` line
- **WHEN** `epic-amend-check <slug>` runs
- **THEN** a `protected-section header` finding line prints and the exit
  code is 4

#### Scenario: Epic absent at the base is an error, not a finding
- **GIVEN** an epic file that exists only on the current branch
- **WHEN** `epic-amend-check <slug>` runs
- **THEN** the verb exits non-zero with an error stating the epic does not
  exist at the base, and the exit code is not 4

#### Scenario: The verb never writes
- **WHEN** `epic-amend-check <slug>` runs with any mix of findings
- **THEN** no file under the repository is modified

#### Scenario: Store-resident epic is read from the store's repository
- **GIVEN** a consuming repo whose `store_root` resolves the epic into a
  separate git repository, with an uncommitted amendable edit to the store's
  epic file
- **WHEN** `epic-amend-check <slug>` runs with `--root` naming the consuming
  repo
- **THEN** the base version is read from the store repository's history and
  the verb reports clean with exit 0

#### Scenario: Store-side protected edit is still a finding
- **GIVEN** the same store layout with an uncommitted edit to the store
  epic's `## Design`
- **WHEN** `epic-amend-check <slug>` runs with `--root` naming the consuming
  repo
- **THEN** a `protected-section ## Design` finding line prints and the exit
  code is 4

#### Scenario: Non-git store is an error naming the epic's directory
- **GIVEN** a `store_root` resolving the epic outside any git work tree
- **WHEN** `epic-amend-check <slug>` runs
- **THEN** the verb exits non-zero, not 4, with an error naming the epic's
  directory rather than the invocation root
