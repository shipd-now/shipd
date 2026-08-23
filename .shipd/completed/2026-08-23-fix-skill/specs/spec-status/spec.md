## ADDED Requirements

### Requirement: Related-artifacts search verb
id: related-verb

The status CLI SHALL provide `related <term> [<term>...]` ranking the spec
library's artifacts by case-insensitive term-hit count: for each artifact, the
sum over all terms of substring occurrence counts across the artifact's files,
searching the resolved content directory's `verified/<slug>/spec.md` (kind
`verified`), `planned/<slug>/` artifact files (`plan.md`, `tasks.md`, delta
`specs/*/spec.md`; kind `planned`), `completed/*-<slug>/` artifact files (kind
`completed`, the slug printed with its `YYYY-MM-DD-` prefix stripped),
`research/<slug>/report.md` (kind `research`), and `epics/<slug>/epic.md`
(kind `epic`), and — where a workspace is discoverable — the workspace wiki
store's `wiki/<slug>.md` pages (kind `wiki`). The CLI SHALL print one keyed
block per matching artifact (`kind:`, `slug:`, `score:`, `path:`, the path
relative to the root when inside it and absolute otherwise) in descending
score order with ties broken by kind then slug, SHALL omit artifacts with no
hits, SHALL cap the printed blocks at ten followed by a single line naming the
count of remaining matches when more matched, and SHALL accept a `--json`
flag emitting exactly one JSON array of objects with those four keys instead.
If no artifact matches, then the CLI SHALL exit non-zero with a single
`Error:` line. Where no workspace or wiki store is discoverable, the CLI
SHALL skip the wiki surface silently and still search every other surface;
a missing corpus directory SHALL likewise be skipped without error.

#### Scenario: Matches print ranked keyed blocks
- **WHEN** `related export` runs in a repo where a verified capability's
  spec.md contains `export` three times and a completed change's plan.md
  contains it once
- **THEN** both artifacts print as keyed blocks with `kind:`, `slug:`,
  `score:`, and `path:`, the verified capability first

#### Scenario: Completed slug feeds the cat verb
- **WHEN** `related <term>` matches only `completed/2026-08-14-my-change/`
- **THEN** the block prints `slug: my-change`, so `cat change my-change`
  reads the match

#### Scenario: JSON mode is one array
- **WHEN** `related export --json` runs with at least one match
- **THEN** stdout parses as exactly one JSON array whose objects carry
  `kind`, `slug`, `score`, and `path`

#### Scenario: Output caps at ten with a remainder line
- **WHEN** `related <term>` matches twelve artifacts
- **THEN** exactly ten keyed blocks print, followed by one line naming the
  two remaining matches

#### Scenario: No match is an error
- **WHEN** `related zzz-no-such-term` runs and nothing contains the term
- **THEN** the CLI prints a single `Error:` line to stderr and exits
  non-zero

#### Scenario: Absent workspace degrades silently
- **WHEN** `related <term>` runs in a repo with no discoverable workspace
  and the term hits a verified spec
- **THEN** the verified match prints, no wiki error appears, and the exit
  code is `0`
