## MODIFIED Requirements

### Requirement: Epic header metadata
id: epic-header-metadata
base: 5fe2a03a24b3

An epic's header metadata block SHALL recognize exactly three keys —
`Theme:`, `Initiative:`, and `PRD:` — with kebab-case values; `Theme:` SHALL
be validated against `valid_themes` when `.shipd/config.json` declares a
non-empty vocabulary; `PRD:` SHALL resolve to an existing PRD across the
workspace chain (the engine's PRD resolution) whenever a workspace root is
discoverable, with an unresolvable value rejected naming the expected path,
and SHALL be skipped silently when no workspace is discoverable (a bare CI
checkout), so repo lint never depends on files outside the repository; and any other key (including `Profile:`
and `Epic:`) SHALL be rejected.

#### Scenario: Epic carries theme and initiative
- **WHEN** an epic header carries `Theme: reliability` and
  `Initiative: mvp-readiness`
- **THEN** both are parsed as the epic's metadata and accepted

#### Scenario: Profile on an epic is rejected
- **WHEN** an epic header carries `Profile: lite`
- **THEN** tooling reports an unrecognized-key error

#### Scenario: Epic carries a resolving PRD link
- **WHEN** an epic header carries `PRD: mobile-push` and a workspace-chain
  member hosts `prds/mobile-push/prd.md`
- **THEN** the line is parsed as the epic's metadata and accepted

#### Scenario: Unresolvable PRD is rejected
- **WHEN** an epic header carries `PRD: no-such-prd` and no chain member
  hosts that PRD
- **THEN** tooling reports the unresolvable reference naming the expected
  `prd.md` path

#### Scenario: Workspace-less checkout skips PRD resolution
- **WHEN** an epic carrying `PRD: mobile-push` lints in a checkout with no
  discoverable workspace
- **THEN** no PRD-resolution error is reported and lint is otherwise
  unchanged
