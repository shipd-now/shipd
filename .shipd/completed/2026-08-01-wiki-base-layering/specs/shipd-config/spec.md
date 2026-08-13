## ADDED Requirements

### Requirement: Wiki base store key
id: wiki-base-key

The configuration MAY declare `wiki_base`: a non-empty string path (with `~`
expansion) naming the durable base wiki store directory layered beneath a
workspace's own wiki store, resolved through the standard layered per-key
merge. The expanded value SHALL be an absolute path; if the declared value is
not a non-empty string or does not expand to an absolute path, then the
consuming verb SHALL exit non-zero with an error naming `wiki_base`. When the
key is undeclared, there SHALL be no base layer. When the resolved base equals
the consuming workspace's own store directory, consumers SHALL treat the base
as undeclared.

#### Scenario: Declared key resolves expanded
- **GIVEN** a config layer declaring `wiki_base: "~/projects/.shipd/wiki"`
- **WHEN** the key is resolved
- **THEN** the result is the absolute expanded path to that directory

#### Scenario: Undeclared key means no base layer
- **WHEN** no layer declares `wiki_base`
- **THEN** resolution yields no base store and no error is raised

#### Scenario: Malformed value errors
- **WHEN** `wiki_base` is declared as a relative path, an empty string, or a
  non-string and a consuming verb runs
- **THEN** the verb exits non-zero with an error naming `wiki_base`

#### Scenario: Self-referential base is no base
- **GIVEN** `wiki_base` resolving to the workspace's own store directory
- **WHEN** a consumer resolves the base layer
- **THEN** it behaves as though the key were undeclared
