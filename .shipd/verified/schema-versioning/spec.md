# schema-versioning

### Requirement: Declared artifact schema version
id: schema-version-declaration

The engine SHALL declare the artifact grammar's version as a three-part
semver constant `SCHEMA_VERSION` in `spec_common`, independent of the plugin
version, and SHALL read a repo's grammar version from a one-line marker file
named `schema` in the resolved content directory. If the marker is absent,
then the repo's version SHALL read as `1.0.0`; if the marker's content is
not three dot-separated integers, then reading it SHALL raise an error
naming the file.

#### Scenario: Absent marker reads as the baseline
- **GIVEN** a repo with the content layout and no `schema` marker
- **WHEN** the engine resolves the repo's schema version
- **THEN** it reads `1.0.0` and no error is raised

#### Scenario: Marker in an external store is honored
- **GIVEN** a config declaring a `store_root` whose store carries a `schema`
  marker
- **WHEN** the engine resolves the repo's schema version
- **THEN** the store's marker value is the answer

#### Scenario: Malformed marker is a clear error
- **GIVEN** a `schema` marker holding `one.two`
- **WHEN** the engine resolves the repo's schema version
- **THEN** an error names the marker file

### Requirement: Schema compatibility gate
id: schema-compat-gate

When an engine verb that reads or writes artifacts runs against a repo whose
schema major differs from `SCHEMA_VERSION`'s major, the engine SHALL exit
with an error naming the repo's version, the engine's version, and the
remedy, before touching any artifact. When the majors match and the repo's
minor is greater than the engine's, the engine SHALL print one stderr
warning and proceed. The gate SHALL apply at the entry points of the status,
emit, merge, lint, and gate scripts, and in the engine binary before its
`list` and `metrics` verbs reach the engine seam — `list` calls it
in-process and `metrics` executes a script no other entry gates, so the
binary is where both refuse; `init` SHALL be exempt (it stamps instead),
and the doctor SHALL report a mismatch as a check result rather than failing
to run.

#### Scenario: Major mismatch refuses before work
- **GIVEN** a repo whose marker reads `2.0.0` under an engine at `1.x`
- **WHEN** any artifact read verb runs
- **THEN** it exits non-zero naming `2.0.0`, the engine's version, and the
  remedy, and no artifact is read or written

#### Scenario: The binary's in-process read verbs are gated
- **GIVEN** a repo whose marker reads a different major
- **WHEN** `shipd list verified` or `shipd metrics` runs against it
- **THEN** each exits non-zero naming both versions and prints no artifact
  rows

#### Scenario: Newer minor warns and proceeds
- **GIVEN** a repo whose marker reads a same-major, higher-minor version
- **WHEN** an artifact read verb runs
- **THEN** one warning line reaches stderr and the verb completes normally

#### Scenario: Matching version is silent
- **GIVEN** a repo whose marker equals `SCHEMA_VERSION`
- **WHEN** an artifact read verb runs
- **THEN** no schema output is produced

### Requirement: Marker stamping on writes
id: schema-marker-stamping

The engine SHALL stamp the `schema` marker with `SCHEMA_VERSION` when
`init` scaffolds the layout, when an emit installs artifacts, and when a
merge archives a change — but only while the marker is absent or carries a
same-major, older version. The engine SHALL NOT rewrite a marker across a
major difference.

#### Scenario: Init stamps a fresh repo
- **WHEN** `init` scaffolds a repo with no marker
- **THEN** the `schema` marker exists holding `SCHEMA_VERSION`

#### Scenario: Same-major older marker advances on write
- **GIVEN** a marker holding a same-major, lower-minor version
- **WHEN** an emit installs a change
- **THEN** the marker afterwards holds `SCHEMA_VERSION`

#### Scenario: Cross-major marker is never rewritten
- **GIVEN** a marker holding a different major
- **WHEN** any stamping write path runs
- **THEN** the marker's content is unchanged
