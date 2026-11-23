# headless-reference — external-loaders delta

## ADDED Requirements

### Requirement: External-loader manifest
id: external-loader-manifest

`plugins/s/external-loaders.json` SHALL list the shipd files, as paths
relative to `plugins/s/`, and the `##` headings of each, that loaders outside
the repository read by name, starting with
`skills/ask/references/headless.md` and its four headings. A unit test in the
engine's test suite SHALL fail when a listed file or a listed heading
disappears, and its message SHALL say that the loss breaks an external loader.
`AGENTS.md` SHALL document the manifest in one place.

#### Scenario: A removed heading fails the test
- **WHEN** a listed `##` heading is renamed in `headless.md`
- **THEN** the manifest test fails naming the heading and file

#### Scenario: A removed file fails the test
- **WHEN** a listed file is moved or deleted
- **THEN** the manifest test fails naming the file

#### Scenario: The current tree passes
- **WHEN** the manifest test runs on the current tree
- **THEN** it passes

