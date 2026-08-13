## MODIFIED Requirements

### Requirement: Merge and archive replace OpenSpec archiving
id: merge-and-archive-replace-openspec-archiving
base: e9ae62121f09

After all tasks are complete and verification passes, build SHALL apply the
change with `spec_merge.py` — merging the delta specs into `am/verified/` and
moving the change directory to `am/completed/` — instead of `openspec archive`.
Build SHALL NOT invoke the OpenSpec CLI at any phase.

#### Scenario: Completed build merges via the engine
- **WHEN** verification passes for a completed change
- **THEN** build runs `spec_merge.py`, the master library reflects the deltas,
  and the change moves to `am/completed/`

#### Scenario: No OpenSpec dependency
- **WHEN** `/s:build` runs end-to-end in a repo without the OpenSpec CLI
  installed
- **THEN** every phase completes using only the plugin's own scripts
