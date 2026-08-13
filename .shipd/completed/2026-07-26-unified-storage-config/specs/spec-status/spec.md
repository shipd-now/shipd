## ADDED Requirements

### Requirement: Config-show verb
id: config-show-verb

The status CLI SHALL provide `config-show` printing the resolved layered
configuration: each effective top-level key with the path of the layer that
supplied it (or `default`), the resolved content directory name, and the
workspace root when one is discoverable (or a note that none is). The verb
SHALL NOT require a discoverable workspace and SHALL exit zero on a
default-only resolution.

#### Scenario: Provenance is printed per key
- **GIVEN** the repo layer declares `valid_themes` and the workspace layer
  declares `workspace`
- **WHEN** `config-show` runs
- **THEN** each key is listed with the config file path that supplied it

#### Scenario: Defaults-only still succeeds
- **WHEN** `config-show` runs where no `.shipd-config.json` exists in any layer
- **THEN** the content directory prints as `.am`, keys show `default`, and
  the exit code is zero

### Requirement: Epic initiative header verb
id: epic-set-initiative-verb

The status CLI SHALL provide `epic-set-initiative <epic> <initiative>`
writing `Initiative: <initiative>` into the epic's header metadata block,
replacing any existing `Initiative:` line and preserving all other header
and body content. An unknown epic SHALL be a non-zero error. The verb SHALL
validate the value is a kebab-case slug and SHALL leave status derivation
untouched.

#### Scenario: Initiative line is written metadata-preservingly
- **GIVEN** an epic whose header carries `Theme: reliability` and no
  `Initiative:` line
- **WHEN** `epic-set-initiative reporting-overhaul mvp-readiness` runs
- **THEN** the header carries both `Theme: reliability` and
  `Initiative: mvp-readiness` and the body is unchanged

#### Scenario: Existing initiative is replaced, never duplicated
- **WHEN** the verb runs on an epic already carrying an `Initiative:` line
- **THEN** exactly one `Initiative:` line remains, holding the new value

## MODIFIED Requirements

### Requirement: Workspace init verb
id: workspace-init-verb
base: 519440f1f0d4

The status CLI SHALL provide `workspace-init <path>` which initializes a
workspace at the given directory through the engine's workspace
initialization — declaring `workspace` in `<path>/.shipd-config.json` — and
prints the created workspace root on success. If initialization refuses or
errors (a workspace already discoverable from the target, or a missing
target directory), then the CLI SHALL exit non-zero with that error. Unlike
the other workspace verbs, `workspace-init` SHALL NOT require a discoverable
workspace to run.

#### Scenario: Init verb creates and prints the root
- **GIVEN** an existing directory with no discoverable workspace
- **WHEN** `workspace-init <path>` runs against it
- **THEN** `.shipd-config.json` declares `workspace` there, the created root is
  printed, and the exit code is zero

#### Scenario: Init verb refuses under an existing workspace
- **WHEN** `workspace-init <path>` runs where a workspace root is already
  discoverable from `<path>`
- **THEN** the CLI exits non-zero with an error naming the existing root
