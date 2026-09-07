## ADDED Requirements

### Requirement: Superset search verb
id: search-verb

The status CLI SHALL provide `search <term> [<term>...]` ranking a superset
corpus by the same case-insensitive term-hit scoring as `related`: every
surface and record the `related` corpus yields (verified, planned, completed,
research, docs, epic, wiki — root plus worktrees, deduped root-first),
extended with two additional surfaces. Where a workspace anchor resolves
(through the same resolution seam the wiki surface uses), the CLI SHALL
search each `initiatives/<slug>/brief.md` under the anchor's resolved content
directory as kind `initiative`; any anchor-resolution failure SHALL skip the
surface silently. Where the invocation root is a git work tree, the CLI SHALL
search the files `git ls-files` enumerates at the invocation root as kind
`code`, each record's slug its root-relative path — skipping files under the
invocation root's resolved content directory, files whose first 8192 bytes
contain a NUL byte, files larger than 1 MiB, and unreadable files; where git
is unavailable or exits non-zero, the CLI SHALL skip the code surface
silently and still search every other surface.

The CLI SHALL print matches in the same output contract as `related`: one
keyed block (`kind:`, `slug:`, `score:`, `path:`) per matching artifact in
descending score order with ties broken by kind then slug, artifacts with no
hits omitted, at most ten blocks followed by a single remainder line when
more matched, a `--json` flag emitting exactly one JSON array of objects with
those four keys instead, and — if no artifact matches — a non-zero exit with
a single `Error:` line. The `related` verb's own corpus and output SHALL
remain unchanged by this verb.

#### Scenario: Tracked code files are searched
- **WHEN** `search export` runs in a git repo whose tracked `src/report.py`
  contains `export` twice
- **THEN** a block prints with `kind: code`, `slug: src/report.py`, and
  `score: 2`

#### Scenario: Content-directory files are not code records
- **WHEN** `search <term>` runs where the term appears only in the tracked
  `verified/<slug>/spec.md` under the resolved content directory
- **THEN** the match prints as `kind: verified` only, with no `kind: code`
  block for the same file

#### Scenario: Binary files are skipped
- **WHEN** `search <term>` runs in a git repo whose only tracked file
  containing the term bytes carries a NUL byte in its first 8192 bytes
- **THEN** no block prints for that file and the CLI reports no match for
  the term

#### Scenario: Initiative briefs are searched
- **WHEN** `search onboarding` runs where the resolved workspace anchor's
  `initiatives/faster-onboarding/brief.md` contains `onboarding`
- **THEN** a block prints with `kind: initiative` and
  `slug: faster-onboarding`, its `path:` naming the brief

#### Scenario: Related surfaces still rank
- **WHEN** `search export` runs where a verified capability's spec.md and a
  tracked code file both contain `export`
- **THEN** both print as keyed blocks, ordered by descending score

#### Scenario: Non-git root degrades to the other surfaces
- **WHEN** `search export` runs in a root that is not a git work tree and
  the term hits a verified spec
- **THEN** the verified match prints, no git error appears, and the exit
  code is `0`

#### Scenario: JSON mode is one array
- **WHEN** `search export --json` runs with at least one match
- **THEN** stdout parses as exactly one JSON array whose objects carry
  `kind`, `slug`, `score`, and `path`

#### Scenario: Output caps at ten with a remainder line
- **WHEN** `search <term>` matches twelve records
- **THEN** exactly ten keyed blocks print, followed by one line naming the
  two remaining matches

#### Scenario: No match is an error
- **WHEN** `search zzz-no-such-term` runs and nothing contains the term
- **THEN** the CLI prints a single `Error:` line to stderr and exits
  non-zero
