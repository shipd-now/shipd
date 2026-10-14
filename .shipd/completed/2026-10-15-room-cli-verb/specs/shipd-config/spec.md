## ADDED Requirements

### Requirement: Room configuration key
id: room-config-key

The configuration MAY declare `room`: a JSON object whose recognized members
are `agent` (a non-empty string, the name this harness's agent posts under
when neither `--agent` nor `SHIPD_ROOM_AGENT` supplies one) and `max_rounds`
(an integer of at least 1, the turn cap a task reaches before a reply posts
`failed` with reason `round-cap`; default 6), resolved through the standard
layered per-key merge. `room` SHALL be a member of
`spec_common.RECOGNIZED_CONFIG_KEYS`, SHALL be documented as a `// room`
entry in the copyable config example, and SHALL carry a row in the
`docs/customise.md` key table. The engine SHALL expose the resolved value
through a stdlib-only `resolve_room(root)` accessor in `spec_common`
returning `(agent, max_rounds)` with `agent` `None` when no layer declares
it. If the declared value is not an object, or `agent` is present and not a
non-empty string, or `max_rounds` is present and not an integer of at least
1, then the accessor SHALL raise `ConfigError` naming `room`, the offending
member, and the config file that supplied it. Members other than `agent`
and `max_rounds` SHALL be ignored.

#### Scenario: Undeclared key yields the defaults
- **WHEN** `resolve_room` runs from a repo whose layers declare no `room`
- **THEN** it returns `(None, 6)`

#### Scenario: Workspace declaration governs a member repo
- **GIVEN** a workspace root's `.shipd-config.json` declaring
  `"room": {"agent": "claude-mikkel", "max_rounds": 4}` and a member repo
  beneath it declaring no `room`
- **WHEN** `resolve_room` runs from the member repo
- **THEN** it returns `("claude-mikkel", 4)`

#### Scenario: Bad member is an error naming the file
- **WHEN** a layer declares `"room": {"max_rounds": 0}`
- **THEN** `resolve_room` raises `ConfigError` whose message names `room`,
  `max_rounds`, and that layer's config path

#### Scenario: Example and guide stay in step with the registry
- **WHEN** the config-sample and customise-guide drift guards run
- **THEN** both pass with `room` documented in the example and present in
  the guide's key table
