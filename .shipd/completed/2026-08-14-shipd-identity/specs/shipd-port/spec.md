## ADDED Requirements

### Requirement: Plugin and marketplace manifests carry the shipd identity
id: identity-manifests

The shipd marketplace manifest SHALL name the marketplace `shipd` and declare a
single plugin named `s` sourced from `./plugins/s`. The plugin manifest SHALL
name the plugin `s` and carry a version one patch increment above the version
read from shipd's plugin manifest at the time this change runs. Neither
manifest SHALL contain a bare `am` as a name or keyword.

#### Scenario: Marketplace names shipd and sources plugins/s
- **WHEN** the shipd marketplace manifest is parsed
- **THEN** its marketplace name is `shipd`, its single plugin entry is named `s`,
  and that entry's source is `./plugins/s`

#### Scenario: Plugin manifest names s and advances the version
- **WHEN** the shipd plugin manifest is parsed and compared with shipd's
- **THEN** the shipd plugin is named `s` and its version is one patch increment
  above shipd's

#### Scenario: No bare am identity survives
- **WHEN** both manifests' name and keyword fields are inspected
- **THEN** none of them is the bare string `am`

### Requirement: Settings enable the shipd plugin and statusline
id: identity-settings

The shipd repository's Claude Code settings SHALL invoke the statusline from the
`plugins/s/` path, enable the `s@shipd` plugin, and declare `shipd` as a
directory-source marketplace at the repository root.

#### Scenario: Statusline points at the ported script
- **WHEN** the settings file's statusline command is read
- **THEN** it invokes the script under `plugins/s/integrations/`

#### Scenario: The shipd plugin and marketplace are declared
- **WHEN** the settings file's enabled-plugins and known-marketplaces entries are
  read
- **THEN** `s@shipd` is enabled and a `shipd` marketplace is declared as a
  directory source

### Requirement: The shipd plugin installs and its skills load under /s:
id: identity-plugin-loads

The `s@shipd` plugin SHALL install from the local marketplace registration, and
its skills SHALL be invocable under the `/s:` namespace in a session started
after the install.

#### Scenario: Plugin installs from the local marketplace
- **WHEN** the shipd marketplace is registered and `s@shipd` is installed
- **THEN** the install reports success and a cache snapshot exists for the
  manifest's version

#### Scenario: Skills load under the s namespace
- **WHEN** a session is started in the shipd repository after the install
- **THEN** the plugin's skills are listed under `/s:` and none is listed under
  `/s:` from this marketplace

#### Scenario: A loaded skill reaches a real engine script
- **WHEN** a `/s:` skill that shells out to the engine is invoked in that session
- **THEN** the engine script under `plugins/s/skills/build/scripts/` runs and
  returns its normal output
