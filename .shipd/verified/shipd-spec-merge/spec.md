# shipd-spec-merge

### Requirement: Deterministic keyed merge
id: deterministic-keyed-merge
The merge engine SHALL apply a change's delta specs into the master library by
matching each delta requirement to a master requirement using exact `id` slug
equality only. It SHALL NOT use similarity, fuzzy matching, or any language model
to decide which requirement a delta operation targets. The merge SHALL be pure
and reproducible: the same delta against the same master SHALL always produce the
same result.

#### Scenario: Delta matches master by id, not by text
- **WHEN** a `## MODIFIED Requirements` entry has `id: enforce-sso-timeout` and a
  reworded title
- **THEN** the engine replaces the master requirement whose `id` is
  `enforce-sso-timeout` and does not consult any other requirement's text

### Requirement: ADDED operation
id: added-operation
For each entry under `## ADDED Requirements`, the engine SHALL insert the
requirement into the target capability. If a requirement with that `id` already
exists in the master, the engine SHALL overwrite it with the incoming content and
emit a warning naming the `id` (take-newer semantics; never a hard failure).

#### Scenario: New id is inserted
- **WHEN** an ADDED entry has an `id` absent from the master
- **THEN** the requirement is appended to the capability's master spec

#### Scenario: ADDED collides with an existing id
- **WHEN** an ADDED entry has an `id` that already exists in the master
- **THEN** the engine overwrites the existing requirement and emits a warning
  identifying the colliding `id`

### Requirement: MODIFIED operation
id: modified-operation
For each entry under `## MODIFIED Requirements`, the engine SHALL replace the
matching master requirement's content with the incoming content. If no
requirement with that `id` exists in the master, the engine SHALL insert the
incoming content and emit a warning (take-newer semantics).

#### Scenario: Existing requirement is replaced
- **WHEN** a MODIFIED entry's `id` exists in the master
- **THEN** the master requirement's body and scenarios are replaced by the
  incoming content

#### Scenario: MODIFIED target is missing
- **WHEN** a MODIFIED entry's `id` is absent from the master
- **THEN** the engine inserts the incoming requirement and emits a warning that
  the modified target was not found

### Requirement: REMOVED operation
id: removed-operation
For each entry under `## REMOVED Requirements`, the engine SHALL delete the
matching master requirement. Each REMOVED entry SHALL include a `Reason` and a
`Migration` note. If no requirement with that `id` exists, the engine SHALL treat
the removal as a no-op and emit a warning.

#### Scenario: Requirement is deleted
- **WHEN** a REMOVED entry's `id` exists in the master and includes Reason and
  Migration
- **THEN** the requirement is removed from the capability's master spec

#### Scenario: REMOVED target is missing
- **WHEN** a REMOVED entry's `id` is absent from the master
- **THEN** the engine leaves the master unchanged and emits a warning

### Requirement: RENAMED operation
id: renamed-operation
For each entry under `## RENAMED Requirements` (FROM/TO id pair), the engine SHALL
re-key the master requirement from the old `id` to the new `id`. If the old `id`
is absent or the new `id` already exists, the engine SHALL apply the rename
best-effort under take-newer semantics and emit a warning.

#### Scenario: Requirement is re-keyed
- **WHEN** a RENAMED entry maps `FROM: sso-timeout` `TO: enforce-sso-timeout` and
  `sso-timeout` exists while `enforce-sso-timeout` does not
- **THEN** the master requirement's `id` becomes `enforce-sso-timeout`

### Requirement: Base-hash concurrency check
id: base-hash-concurrency-check
For each MODIFIED or REMOVED entry, the engine SHALL compare the entry's `base:`
hash to the current content hash of the matching master requirement. On a
mismatch the engine SHALL still apply the incoming operation (take-newer) and
SHALL emit a warning naming the `id` and both the expected and actual hashes, so
a stale-base overwrite is always reported rather than silent.

#### Scenario: Base hash matches
- **WHEN** a MODIFIED entry's `base:` equals the master requirement's current
  content hash
- **THEN** the engine applies the modification with no concurrency warning

#### Scenario: Base hash is stale
- **WHEN** a MODIFIED entry's `base:` differs from the master requirement's
  current content hash
- **THEN** the engine applies the incoming content and emits a warning reporting
  the `id`, the expected base hash, and the actual master hash

### Requirement: Content hash definition
id: content-hash-definition
The engine SHALL compute a requirement's content hash deterministically over its
normalized normative body and scenarios, excluding the `id:` and `base:`
metadata lines and insignificant whitespace, so that identical behavior yields an
identical hash across machines and runs and a rename (re-keyed `id`) does not
change the hash.

#### Scenario: Cosmetic whitespace does not change the hash
- **WHEN** two requirement blocks differ only in trailing whitespace or blank
  lines between sections
- **THEN** they produce the same content hash

### Requirement: Deterministic output and warning summary
id: deterministic-output-and-warning-summary
After applying all operations, the engine SHALL rewrite each affected master file
with a stable, reproducible ordering of requirements, and SHALL emit all warnings
as a machine-readable summary (in addition to human-readable output) so a caller
such as the build report can surface them.

#### Scenario: Warnings are machine-readable
- **WHEN** a merge produces one or more warnings
- **THEN** the engine outputs a structured summary listing each warning's `id`
  and kind that a caller can parse and display
