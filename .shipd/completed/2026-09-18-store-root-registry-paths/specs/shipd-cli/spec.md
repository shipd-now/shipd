## ADDED Requirements

### Requirement: Doctor external-store check
id: doctor-store-check

The `doctor` preflight SHALL report a `store` check line naming the external
store the working directory resolves, positioned directly after the `wiki` line
in the check roster. Where the resolved configuration declares no `store_root`,
the check SHALL report `ok` stating that the content directory is in-repo.
Where `store_root` is declared, the check SHALL report `ok` naming the resolved
absolute content directory. If a directory exists at the store root joined with
the basename fallback path while the resolved content directory does not exist,
then the check SHALL report `warn` naming both paths and a `git mv` remedy. The
check SHALL mutate nothing and SHALL never move, create, or delete a store
directory. If the configuration is malformed, then the check SHALL report `ok`
carrying the error as its detail, leaving the `config` check to own config
failures.

#### Scenario: No store declared reports in-repo
- **GIVEN** a repository whose resolved configuration declares no `store_root`
- **WHEN** the preflight runs
- **THEN** the `store` line reports `ok` and states the content directory is
  in-repo

#### Scenario: Resolved store is named
- **GIVEN** a repository resolving an external store that exists
- **WHEN** the preflight runs
- **THEN** the `store` line reports `ok` naming the resolved absolute content
  directory

#### Scenario: Stranded flat folder warns with both paths
- **GIVEN** a declared registry member whose store root holds a directory at the
  basename fallback path while the registry-path directory is absent
- **WHEN** the preflight runs
- **THEN** the `store` line reports `warn`, names the existing basename path and
  the resolved registry path, and names a `git mv` remedy

#### Scenario: The check moves nothing
- **WHEN** the preflight runs against a stranded flat folder
- **THEN** no directory is created, moved, or deleted, and the preflight's exit
  code is unchanged by the warning

#### Scenario: Malformed config is reported, not double-failed
- **GIVEN** a repository whose configuration fails to resolve
- **WHEN** the preflight runs
- **THEN** the `store` line reports `ok` carrying the error as its detail
