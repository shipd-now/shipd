## ADDED Requirements

### Requirement: Skill prompt path notation
id: skill-prompt-path-notation

Literal `.shipd/` path references in the plugin's skill prompt files
(`plugins/s/skills/**/*.md`) SHALL be read as denoting the repo's resolved
content directory (default `.shipd`), mirroring the master library's
path-notation convention. Every prompt line carrying such a reference SHALL
either be self-annotating — a `~/.shipd` home path, a `$SANDBOX` onboarding
path, a `default`-annotated mention, or a mention naming the content
directory — or belong to a file that carries the canonical notation rule
(marker text `denote the repo's resolved content directory`);
`plugins/s/skills/onboard/SKILL.md` SHALL be exempt because its sandbox always
uses the default layout. Runnable commands shown in prompt text SHALL resolve
the content directory through the engine (`config-show`'s `content-dir:` line,
or a mediated `cat` verb) rather than hardcoding `.shipd`. The engine's test
suite SHALL enforce the line-level contract and fail naming each offending
file and line.

#### Scenario: Notation rule covers a file's shorthand
- **GIVEN** `plugins/s/skills/build/SKILL.md` carries the canonical notation
  rule
- **WHEN** the prompt-notation test scans its `.shipd/` mentions
- **THEN** the file passes without rewording each mention

#### Scenario: Unannotated literal fails the suite
- **WHEN** a non-exempt prompt file with no notation rule gains a line
  mentioning `.shipd/` with no self-annotation
- **THEN** the prompt-notation test fails naming that file and line

#### Scenario: Fixed and sandbox paths are exempt
- **WHEN** a prompt line references `~/.shipd/onboarding/state.json` or
  `$SANDBOX/.shipd/planned/`
- **THEN** the test passes that line without requiring the notation rule

#### Scenario: Runnable listing resolves the directory
- **WHEN** `plugins/s/skills/build/SKILL.md` instructs listing existing
  capabilities and in-flight changes
- **THEN** the command it shows resolves the content directory from
  `config-show`'s `content-dir:` line before listing, rather than hardcoding
  `.shipd/verified/` or `.shipd/planned/`
