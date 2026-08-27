## MODIFIED Requirements

### Requirement: Wiki base store key
id: wiki-base-key
base: 7fbb54f5a607

The configuration MAY declare `wiki_base`: a non-empty string path (with `~`
expansion) naming the durable base wiki store directory layered beneath the
workspace chain's own stores, resolved through the standard layered per-key
merge. The expanded value SHALL be an absolute path; if the declared value is
not a non-empty string or does not expand to an absolute path, then the
consuming verb SHALL exit non-zero with an error naming `wiki_base`. When the
key is undeclared, there SHALL be no base layer. When the resolved base equals
the store directory of any member of the consuming workspace chain, consumers
SHALL treat the base as undeclared, so a base that is also an enclosing
workspace is searched once rather than twice.

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

#### Scenario: A base already in the chain is no base
- **GIVEN** nested workspaces where `wiki_base` resolves to the outer
  workspace's store directory
- **WHEN** a consumer in a repo under the inner workspace resolves the base
  layer
- **THEN** it behaves as though the key were undeclared
