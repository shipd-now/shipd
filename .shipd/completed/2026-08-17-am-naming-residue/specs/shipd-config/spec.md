## MODIFIED Requirements

### Requirement: Spec-library path notation
id: spec-library-path-notation
base: 0c4fc18c3d3f

Literal `.shipd/` path prefixes appearing in master-library requirement text
SHALL be read as denoting the configured content directory (default `.shipd`),
so requirements that reference canonical locations incidentally remain
correct when the directory is renamed. The retired `am/` prefix notation
SHALL no longer appear in master-library requirement text.

#### Scenario: Notation follows the configured name
- **GIVEN** a repo whose config declares `dir: "specs"`
- **WHEN** a requirement elsewhere references `.shipd/planned/<change>/`
- **THEN** tooling and readers resolve it as `specs/planned/<change>/`

#### Scenario: No retired prefix survives in the library
- **WHEN** the master library's requirement texts are scanned for the
  retired `am/` path prefix
- **THEN** no occurrence remains outside the `shipd-port` capability's
  deliberate legacy examples
