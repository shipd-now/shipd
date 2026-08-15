## ADDED Requirements

### Requirement: Shipd README carries the brand, the domain, and the s namespace
id: brand-readme

The shipd README SHALL open with a banner spelling `shipd`, SHALL state the
`shipd.now` domain, and SHALL present the skill table with every invocation
written in the `/s:` namespace. It SHALL NOT contain the string `shipd` or any
`/s:` invocation.

#### Scenario: Banner and domain are present
- **WHEN** the shipd README is read
- **THEN** its opening banner spells `shipd` and the text contains `shipd.now`

#### Scenario: Skill table uses the s namespace
- **WHEN** the README's skill invocations are inspected
- **THEN** every one is written as `/s:<name>`

#### Scenario: No shipd identity remains
- **WHEN** the README is searched for `shipd` and for `/s:`
- **THEN** neither is found

### Requirement: Working instructions describe shipd's own discipline
id: brand-agents-doc

The shipd repository's agent instructions SHALL describe the `shipd` marketplace,
the `s@shipd` plugin and its cache-snapshot refresh, the `.shipd` content
directory, and the `/s:` skills — and every path, command, and marketplace name
they name SHALL resolve in the shipd tree.

#### Scenario: Instructions name the shipd plugin and content directory
- **WHEN** the shipd agent instructions are read
- **THEN** they name the `s@shipd` plugin, the `shipd` marketplace, and the
  `.shipd` content directory

#### Scenario: Every named path resolves
- **WHEN** each repository path named in the agent instructions is checked
  against the shipd tree, excluding the lifecycle directories git creates on
  demand and cannot track while empty (`planned/` and `.worktrees/`)
- **THEN** every one of them exists

### Requirement: Repository hygiene files match a Python repo
id: brand-repo-hygiene

The shipd repository's ignore file SHALL cover the Python and workflow artifacts
the repo actually produces — including its virtualenv, bytecode caches, worktree
directory, and the content directory's runtime state and autopilot output — and
SHALL NOT be the clone's stock Node template.

#### Scenario: Python and workflow artifacts are ignored
- **WHEN** the shipd ignore file is read
- **THEN** it covers bytecode caches, the virtualenv, and the content directory's
  runtime state and autopilot output

#### Scenario: The Node template is gone
- **WHEN** the shipd ignore file is searched for `node_modules` alongside the
  bundler and framework entries the clone shipped with
- **THEN** the stock template's framework-specific entries are absent

### Requirement: Tool-rewritten brand strings are correct
id: brand-ui-strings

The ported delivery board's brand block and the ported statusline's banner
comment SHALL read `shipd`, not `shipd`.

#### Scenario: Board header reads shipd
- **WHEN** the ported board's brand block string is read
- **THEN** it renders `shipd` beside the muted `delivery board` label

#### Scenario: Statusline banner reads shipd
- **WHEN** the ported statusline script's opening comment is read
- **THEN** it names shipd rather than shipd
