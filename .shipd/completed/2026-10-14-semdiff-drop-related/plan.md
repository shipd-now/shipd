# semdiff-drop-related
Status: verified
Theme: spec-engine

## Idea

### Motivation

`semdiff related` has no consumer. The `/s:review` step that called it was
removed in v0.6.275's revert, and no prompt surface has named the subcommand
since — verified across `SKILL.md`, `harness/bodies/review.md` and all eight
files under `references/`, zero mentions.

It is not small. The related-exclusive machinery is **446 lines** of
`semdiff.py`, roughly a quarter of the file, plus **675 lines** of tests. All
of it reachable only by someone hand-typing a subcommand no instruction
mentions.

It was kept at the revert on the argument that a documented CLI surface with
its own requirement and tests is not dead code. That argument does not survive
the question "what uses it". Its one measurement was also unattributable: on
the two PRs it ran against it scored 22.0 where v0.6.260 scored 21.7, and it
never received a three-PR set, so there is no evidence to preserve either.

### Details

The subcommand, its machinery, its tests and its requirement are removed. Two
helpers it shared with live subcommands stay.

### Non-goals

- **Two shared helpers are deliberately kept, and this is the whole risk of
  the change.** `_is_manifest` with `MANIFEST_BASENAMES` and
  `MANIFEST_SUFFIXES` is used by `COHORT_RULES`, which `cmd_files` runs for
  step 1 of every review — removing it would silently stop the `contracts`
  cohort recognising manifests. `_grep_matches` is used by `cmd_context`,
  which step 3 runs. A first reachability pass scanned only function bodies
  and reported both as unused, because `_is_manifest`'s one caller sits in a
  module-level lambda; a whole-file scan corrected it.
- **The tests for `files` and `context` stay.**
  `test_semdiff_files_context.py` covers three live subcommands as well as
  `related`; only the eight related-exclusive classes and the one
  `GrepFailureTest` method that drives `cmd_related` are removed.
- No change to any `/s:review` prompt surface, so no measurement baseline
  moves.
- No change to any other subcommand's behaviour. This is a deletion, and the
  evidence below is that nothing else moved.

## Implementation

Removed from `plugins/s/skills/review/scripts/semdiff.py`: `cmd_related`,
`_find_importers`, `_find_importees`, `_resolve_importee`, `_importee_tokens`,
`_module_terms`, `_exists_with_extension`, `_find_unique_source_file`,
`_file_text_at`, `_proximity_key`, the `RELATED_CAPS` constant, the
`IMPORT_EXTENSIONS` block, the section banner, the `related` subparser and the
usage-header line. 1826 → 1469 lines.

Removed from `plugins/s/skills/review/tests/test_semdiff_files_context.py`:
eight classes — `RelatedTest`, `ImporteeEngineImportFallbackTest`,
`CrossLanguageImporterTest`, `FairShareInvariantTest`,
`FairShareOrderingTest`, `StarvationCountsTest`, `SharedRelatedFileTest`,
`PerFileCapBoundsFreeCandidatesTest` — and
`GrepFailureTest.test_related_dies_rather_than_reporting_zero_importers`.
944 → 269 lines. `FilesCohortTest`, `ContextTest` and the rest of
`GrepFailureTest` stay.

Two docstrings that described `related`'s behaviour are reworded rather than
left describing a subcommand that no longer exists.

### The evidence that nothing used it

Behaviour is compared old script against new script on **identical inputs**,
rather than before-and-after in a working tree whose contents the edit itself
changes — the first attempt at this comparison measured its own diff and
reported three false differences.

| invocation | result |
| --- | --- |
| `files HEAD~3 HEAD~1` | byte-identical, 1803 bytes |
| `diff HEAD~3 HEAD~1` | byte-identical, 127788 bytes |
| `context cmd_files` | byte-identical, 1054 bytes |
| `context _is_manifest` | byte-identical, 1451 bytes |
| `lint HEAD~3 HEAD~1` | byte-identical, 413 bytes |
| `doctor` | byte-identical, 168 bytes |
| `change <slug>` | byte-identical, 93 bytes |

`files` exercises `_is_manifest` through `COHORT_RULES` and `context`
exercises `_grep_matches`, so the two kept helpers are covered by the
comparison rather than only by the reachability argument.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps to the next free number above
whatever `main` carries when this ships. Two changes are in flight ahead of it,
so the implementer reads `main` rather than assuming a figure — merging a
version at or below `main`'s moves the plugin version backwards, which has
already happened twice in this series and is what `version_guard.py` exists to
catch.

## Readiness attestation

### Problem and motivation

A quarter of `semdiff.py` and 675 lines of tests implement a subcommand no
instruction names and no measurement supports.

Evidence, measured in this worktree: zero mentions of `related` across
`SKILL.md`, the harness body and all eight reference files; the
related-exclusive machinery is 446 lines by function-range accounting; the test
file is 944 lines of which 675 are related-exclusive classes.

### Scope and non-goals

In scope: the subcommand and its machinery, its tests, its `related-context`
requirement, two stale docstrings, the version bump.

Out of scope: `_is_manifest` and its constants, `_grep_matches`, the tests for
`files` and `context`, every `/s:review` prompt surface, and every other
subcommand.

### Affected capabilities and files

One capability, one requirement removed: `semantic-review`/`related-context`,
base `2b52c172e564` from `spec_status.py base-hash` here.

Files: `plugins/s/skills/review/scripts/semdiff.py`,
`plugins/s/skills/review/tests/test_semdiff_files_context.py`,
`plugins/s/.claude-plugin/plugin.json`.

Runnable premises measured here: `semdiff.py --help` lists `related` before and
does not after; the module imports cleanly after removal; all seven surviving
subcommands produce byte-identical output old-against-new on identical inputs;
`test_semdiff_files_context.py` passes at 8 tests after the removal.

### No open task-shaping decision

- Whether anything uses it: nothing does, established by a whole-file scan
  after a body-only scan gave a wrong answer, and confirmed empirically by the
  seven-invocation comparison — settled above.
- Which helpers survive: `_is_manifest` with its two constants and
  `_grep_matches`, because `COHORT_RULES` and `cmd_context` call them —
  settled above with the call sites named.
- Whether the test file goes whole: no, it covers three live subcommands —
  settled above.
- What the version becomes: read from `main` at ship time, not assumed,
  because two changes are in flight ahead of this one — settled above.
