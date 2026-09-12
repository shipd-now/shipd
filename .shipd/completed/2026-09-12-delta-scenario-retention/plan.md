# delta-scenario-retention
Status: verified
Theme: reliability

## Idea

Refuse a `MODIFIED` delta that silently drops scenarios its base requirement
carries, unless the delta names each dropped scenario in a `Dropped:` line.

### Motivation

`MODIFIED` replaces a master requirement's whole content, so a delta that
restates only some of its base's scenarios deletes the rest on merge — which
happened in `lint-satisfiability-static`, where a delta carrying two of six
scenarios would have dropped four, including the one pinning a behavior its
own prose still asserted.

### Details

- Add a `Dropped:` metadata line to the `MODIFIED` delta grammar, naming a
  scenario title the entry deliberately removes; repeatable, one title each.
- Add a linter rule: a `MODIFIED` entry whose scenario titles omit any title
  its base master requirement carries is an error, naming each missing title,
  unless a `Dropped:` line names it.
- Strip `Dropped:` at merge, exactly as `base:`, `Reason:` and `Migration:`
  are stripped, so the master never carries delta-only metadata.

Affected capabilities: `shipd-spec-format` (modified), `shipd-spec-lint`
(added), `shipd-spec-merge` (modified). Impact:
`plugins/s/skills/build/scripts/spec_common.py`,
`plugins/s/skills/build/scripts/spec_lint.py`, `.shipd/README.md`, and tests
under `plugins/s/skills/build/tests/`. No new dependencies; the engine stays
stdlib-only.

### Non-goals

- No change to how `MODIFIED` merges — it still replaces the requirement's
  content wholesale. The rule governs what a delta must say before that
  replacement is allowed, not the replacement itself.
- No scenario-level merge or three-way diff. Scenarios are still carried by
  restatement, not tracked individually.
- No matching rule for `ADDED` or `REMOVED` entries, which have no base
  scenarios to retain.
- No retroactive check of the archived changes under `completed/`.

## Implementation

- **Match scenarios by exact title.** The comparison keys on the
  `#### Scenario:` title text, the same handle `Dropped:` names and the
  linter reports. Rejected: matching on body text or a content hash, which
  would fire on every reworded scenario and train authors to ignore the
  rule — the common legitimate edit is rewording a scenario in place, and
  that must stay silent. The cost is that renaming a scenario reads as a drop
  plus an add; the `Dropped:` line is how the author says which it was.
  Verified premise: `spec_common.Scenario` already carries `title` parsed from
  the block header, and `parse_spec`/`parse_delta` already expose
  `Requirement.scenarios`, so no new parsing is required for the comparison
  itself.

- **`Dropped:` is delta-only metadata, parsed like `Reason:`.** Add a
  `dropped` field to `spec_common.Requirement` alongside `reason` and
  `migration`, parsed in `parse_requirement_block`, and omitted by
  `render_requirement`, whose docstring already states that delta-only
  metadata is dropped because the master library never carries it. A
  repeated `Dropped:` line appends, so an entry dropping several scenarios
  names them one per line.
  Verified premise: `render_requirement`'s docstring reads "Delta-only
  metadata (``base:``, ``Reason:``, ``Migration:``) is dropped, because the
  master library never carries it", and it emits only the title, `id:`, and
  `content` — so a new metadata field is excluded by construction.

- **The rule reads the master through the same root as the rest of the
  linter.** A `MODIFIED` entry whose `id` has no master requirement is
  already handled elsewhere (merge inserts it with a warning), so this check
  skips such an entry rather than reporting every scenario as dropped.

- **A `Dropped:` title that the base does not carry is itself an error.**
  Otherwise a stale or misspelled `Dropped:` line silently licenses nothing
  while looking like it licenses something.

Risk: an author facing the error may restate scenarios mechanically without
reading them. The error names each missing title so the restatement is a
copy, not a rewrite, and the `Dropped:` alternative stays one line away.
