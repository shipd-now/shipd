## ADDED Requirements

### Requirement: Clone sources key
id: clone-sources-key

The configuration MAY declare `clone_sources`: a list of directory path
strings (with `~` expansion) naming where the sync planner probes for local
candidate clones, resolved through the standard layered per-key merge.
When the key is undeclared, the candidate set SHALL be empty — the planner
SHALL never fall back to implicit discovery. If the declared value is not a
list of non-empty strings, then the consuming verb SHALL exit non-zero with
an error naming the key.

#### Scenario: Declared sources feed the planner
- **GIVEN** `clone_sources` declaring a directory that contains a clone
  matching a manifest url
- **WHEN** the sync plan is computed
- **THEN** that clone is used as the member's materialization source

#### Scenario: Undeclared key means no probing
- **GIVEN** no layer declares `clone_sources`
- **WHEN** the sync plan is computed for an absent member with a url
- **THEN** the member's action is `clone` (no local candidate is
  discovered)

#### Scenario: Malformed value errors
- **WHEN** `clone_sources` is declared as a string rather than a list and
  the sync verb runs
- **THEN** the verb exits non-zero naming `clone_sources`
