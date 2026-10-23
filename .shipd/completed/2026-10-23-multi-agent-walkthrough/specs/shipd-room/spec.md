## ADDED Requirements

### Requirement: A walkthrough for multi-agent autonomous pull requests
id: multi-agent-walkthrough-doc

The repository SHALL carry `docs/multi-agent-autonomous-prs.md`, a `how-to`
of at most 150 lines that passes `docs_lint.py`. It SHALL name the four
actors and the prerequisites, SHALL give the commands that start the reviewer
listener and the author listener, and SHALL walk the flow step by step with
https://github.com/mikkel-bergmann/unkannybanny/pull/40 as the example. It
SHALL describe review claims and the `room-review/<agent>` merge guard, and
SHALL link to the existing room docs. Every command it shows SHALL match the
current `shipd room run` options.

#### Scenario: The page lints and fits its cap
- **WHEN** `docs_lint.py docs/multi-agent-autonomous-prs.md` runs
- **THEN** it exits 0, and the file has at most 150 lines with the marker
  `<!-- doc-type: how-to -->`

#### Scenario: The listener commands are real
- **WHEN** each `shipd room run` command in the page is compared with
  `shipd room run --help`
- **THEN** every flag it uses exists

#### Scenario: Existing docs point at it
- **WHEN** `docs/multi-agent-pr.md` and `docs/room-run.md` are read
- **THEN** each one's `## See also` section links
  `multi-agent-autonomous-prs.md`
